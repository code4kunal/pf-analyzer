"""
Prospect Service
Handles business logic for prospect management
"""

from sqlalchemy.orm import Session
from sqlalchemy import and_, or_, func, extract
from typing import List, Optional, Dict
from datetime import datetime, date
from models import (
    Prospect, ProspectActivity, ProspectCommunication, User, Customer,
    ProspectStatus, ProspectPriority, ProspectSource
)
from schemas import ProspectCreate, ProspectUpdate
import json

class ProspectService:
    """Service for prospect operations"""

    @staticmethod
    def log_activity(db: Session, prospect_id: int, user_id: int,
                    action: str, description: str, changes: Optional[Dict] = None):
        """Log prospect activity"""
        activity = ProspectActivity(
            prospect_id=prospect_id,
            user_id=user_id,
            action=action,
            description=description,
            changes=changes
        )
        db.add(activity)
        db.commit()

    @staticmethod
    def create_prospect(db: Session, prospect_data: ProspectCreate, current_user: User) -> Prospect:
        """Create a new prospect"""
        prospect = Prospect(
            **prospect_data.dict(exclude_unset=True),
            created_by_id=current_user.id,
            source=prospect_data.source
        )

        db.add(prospect)
        db.commit()
        db.refresh(prospect)

        # Log activity
        ProspectService.log_activity(
            db, prospect.id, current_user.id,
            "CREATED",
            f"Prospect {prospect.full_name} created",
            {"status": prospect.status.value}
        )

        return prospect

    @staticmethod
    def update_prospect(db: Session, prospect_id: int, prospect_data: ProspectUpdate,
                       current_user: User) -> Prospect:
        """Update prospect"""
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            raise ValueError("Prospect not found")

        # Track changes
        changes = {}
        update_data = prospect_data.dict(exclude_unset=True)

        for key, value in update_data.items():
            old_value = getattr(prospect, key)
            if old_value != value:
                # Convert to string for JSON serialization
                if isinstance(old_value, (ProspectStatus, ProspectPriority, ProspectSource)):
                    old_value = old_value.value
                if isinstance(value, (ProspectStatus, ProspectPriority, ProspectSource)):
                    value = value.value
                if isinstance(old_value, datetime):
                    old_value = old_value.isoformat()
                if isinstance(value, datetime):
                    value = value.isoformat()

                changes[key] = {"old": old_value, "new": value}
                setattr(prospect, key, update_data[key])

        db.commit()
        db.refresh(prospect)

        # Log activity if there were changes
        if changes:
            ProspectService.log_activity(
                db, prospect.id, current_user.id,
                "UPDATED",
                f"Prospect {prospect.full_name} updated",
                changes
            )

        return prospect

    @staticmethod
    def convert_to_customer(db: Session, prospect_id: int, current_user: User,
                           relationship_manager_id: Optional[int] = None,
                           copy_notes: bool = True) -> Customer:
        """Convert prospect to customer"""
        prospect = db.query(Prospect).filter(Prospect.id == prospect_id).first()
        if not prospect:
            raise ValueError("Prospect not found")

        if prospect.converted_to_customer_id:
            raise ValueError("Prospect already converted")

        # Create customer from prospect
        customer_data = {
            "full_name": prospect.full_name,
            "email": prospect.email or f"prospect_{prospect.id}@temp.com",  # Email required for customer
            "phone": prospect.phone or "0000000000",  # Phone required for customer
            "alternate_phone": prospect.alternate_phone,
            "annual_income": prospect.estimated_portfolio_value,
            "referral_source": prospect.referral_source,
            "relationship_manager_id": relationship_manager_id or prospect.assigned_to_id,
            "status": "ACTIVE",  # Convert to active customer
            "created_by_id": current_user.id
        }

        # Add custom fields as notes if they exist
        if prospect.custom_fields and copy_notes:
            custom_notes = "\n".join([f"{k}: {v}" for k, v in prospect.custom_fields.items()])
            customer_data["investment_goals"] = custom_notes

        customer = Customer(**customer_data)
        db.add(customer)
        db.flush()  # Get customer ID

        # Update prospect with conversion info
        prospect.converted_to_customer_id = customer.id
        prospect.converted_at = datetime.utcnow()
        prospect.converted_by_id = current_user.id
        prospect.status = ProspectStatus.CONVERTED

        db.commit()
        db.refresh(customer)
        db.refresh(prospect)

        # Log activity
        ProspectService.log_activity(
            db, prospect.id, current_user.id,
            "CONVERTED",
            f"Prospect converted to customer (ID: {customer.id})",
            {"customer_id": customer.id, "customer_name": customer.full_name}
        )

        return customer

    @staticmethod
    def get_existing_emails(db: Session) -> set:
        """Get set of all existing prospect emails"""
        emails = db.query(Prospect.email).filter(Prospect.email.isnot(None)).all()
        return {email[0].lower() for email in emails}

    @staticmethod
    def get_existing_phones(db: Session) -> set:
        """Get set of all existing prospect phones"""
        phones = db.query(Prospect.phone).filter(Prospect.phone.isnot(None)).all()
        return {phone[0] for phone in phones}

    @staticmethod
    def build_filter_query(db: Session, filters: Dict, current_user: User):
        """Build filtered query for prospects"""
        query = db.query(Prospect)

        # Admin sees all, employee sees only assigned (if configured)
        # For now, we'll make it admin-only by default

        # Search filter
        if filters.get('search'):
            search = f"%{filters['search']}%"
            query = query.filter(
                or_(
                    Prospect.full_name.ilike(search),
                    Prospect.email.ilike(search),
                    Prospect.phone.ilike(search),
                    Prospect.company.ilike(search)
                )
            )

        # Status filter (multiple values)
        if filters.get('status'):
            query = query.filter(Prospect.status.in_(filters['status']))

        # Priority filter (multiple values)
        if filters.get('priority'):
            query = query.filter(Prospect.priority.in_(filters['priority']))

        # Source filter (multiple values)
        if filters.get('source'):
            query = query.filter(Prospect.source.in_(filters['source']))

        # Assigned to filter
        if filters.get('assigned_to_id'):
            query = query.filter(Prospect.assigned_to_id == filters['assigned_to_id'])

        # Date range filters
        if filters.get('created_from'):
            query = query.filter(Prospect.created_at >= filters['created_from'])

        if filters.get('created_to'):
            query = query.filter(Prospect.created_at <= filters['created_to'])

        if filters.get('next_followup_from'):
            query = query.filter(Prospect.next_follow_up_date >= filters['next_followup_from'])

        if filters.get('next_followup_to'):
            query = query.filter(Prospect.next_follow_up_date <= filters['next_followup_to'])

        # Estimated value range
        if filters.get('estimated_value_min'):
            query = query.filter(Prospect.estimated_portfolio_value >= filters['estimated_value_min'])

        if filters.get('estimated_value_max'):
            query = query.filter(Prospect.estimated_portfolio_value <= filters['estimated_value_max'])

        # Tags filter (contains any of the tags)
        if filters.get('tags'):
            # This is a JSON field, so we need to check if any tag is in the array
            for tag in filters['tags']:
                query = query.filter(Prospect.tags.contains([tag]))

        # Conversion filter
        if filters.get('is_converted') is not None:
            if filters['is_converted']:
                query = query.filter(Prospect.converted_to_customer_id.isnot(None))
            else:
                query = query.filter(Prospect.converted_to_customer_id.is_(None))

        return query

    @staticmethod
    def get_analytics(db: Session) -> Dict:
        """Get prospect analytics"""

        # Total prospects
        total_prospects = db.query(func.count(Prospect.id)).scalar()

        # By status
        status_counts = db.query(
            Prospect.status,
            func.count(Prospect.id)
        ).group_by(Prospect.status).all()

        by_status = [
            {
                "status": status.value,
                "count": count,
                "percentage": round((count / total_prospects * 100) if total_prospects > 0 else 0, 2)
            }
            for status, count in status_counts
        ]

        # By source with conversion rate
        source_stats = db.query(
            Prospect.source,
            func.count(Prospect.id).label('total'),
            func.count(Prospect.converted_to_customer_id).label('converted')
        ).group_by(Prospect.source).all()

        by_source = [
            {
                "source": source.value,
                "count": total,
                "percentage": round((total / total_prospects * 100) if total_prospects > 0 else 0, 2),
                "conversion_rate": round((converted / total * 100) if total > 0 else 0, 2)
            }
            for source, total, converted in source_stats
        ]

        # By priority
        priority_counts = db.query(
            Prospect.priority,
            func.count(Prospect.id)
        ).group_by(Prospect.priority).all()

        by_priority = {
            priority.value: count
            for priority, count in priority_counts
        }

        # Conversion stats
        total_converted = db.query(func.count(Prospect.id)).filter(
            Prospect.converted_to_customer_id.isnot(None)
        ).scalar()

        conversion_rate = round((total_converted / total_prospects * 100) if total_prospects > 0 else 0, 2)

        # Average time to convert (in days)
        avg_time_to_convert = db.query(
            func.avg(
                func.extract('epoch', Prospect.converted_at - Prospect.created_at) / 86400
            )
        ).filter(Prospect.converted_at.isnot(None)).scalar()

        # Conversion stats by status
        conversion_stats = {}
        for status in ProspectStatus:
            count = db.query(func.count(Prospect.id)).filter(
                and_(
                    Prospect.status == status,
                    Prospect.converted_to_customer_id.isnot(None)
                )
            ).scalar()
            conversion_stats[status.value] = count

        return {
            "total_prospects": total_prospects,
            "by_status": by_status,
            "by_source": by_source,
            "by_priority": by_priority,
            "conversion_stats": conversion_stats,
            "avg_time_to_convert_days": round(avg_time_to_convert, 2) if avg_time_to_convert else None,
            "total_converted": total_converted,
            "conversion_rate": conversion_rate
        }
