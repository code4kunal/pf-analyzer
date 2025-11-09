"""
Intelligent Prospect Import Service
Handles CSV/Excel file parsing with auto-column mapping, validation, and duplicate detection
"""

import pandas as pd
import uuid
import os
from typing import List, Dict, Tuple, Optional
from datetime import datetime
from difflib import SequenceMatcher
from email_validator import validate_email, EmailNotValidError
import re

class ProspectImportService:
    """Service for importing prospects from CSV/Excel files"""

    # Field mapping patterns for intelligent column detection
    FIELD_PATTERNS = {
        "full_name": ["name", "full name", "full_name", "fullname", "client name", "prospect name", "contact name", "contact", "person"],
        "email": ["email", "e-mail", "mail", "email address", "email_address", "e_mail"],
        "phone": ["phone", "mobile", "cell", "telephone", "contact number", "phone number", "mobile number", "phone_number", "mobile_number"],
        "alternate_phone": ["alternate phone", "alt phone", "secondary phone", "phone 2", "alternate_phone", "second phone"],
        "company": ["company", "organization", "org", "firm", "business", "company name", "company_name"],
        "designation": ["designation", "title", "position", "role", "job title", "job_title"],
        "estimated_portfolio_value": ["value", "portfolio", "investment", "aum", "assets", "portfolio value", "net worth", "networth", "estimated value"],
        "notes": ["notes", "comments", "remarks", "description", "note", "comment"],
        "referral_source": ["source", "referred by", "referral", "lead source", "referral_source", "reference"],
        "tags": ["tags", "tag", "categories", "category"],
        "city": ["city", "location", "place"],
        "state": ["state", "province", "region"],
        "address": ["address", "street", "address line"]
    }

    def __init__(self, temp_dir: str = "./temp_imports"):
        """
        Initialize import service

        Args:
            temp_dir: Directory for temporary file storage
        """
        self.temp_dir = temp_dir
        os.makedirs(temp_dir, exist_ok=True)

    def save_temp_file(self, file_content: bytes, filename: str) -> str:
        """
        Save uploaded file temporarily and return unique key

        Args:
            file_content: File bytes
            filename: Original filename

        Returns:
            file_key: Unique identifier for the temp file
        """
        file_key = str(uuid.uuid4())
        file_extension = os.path.splitext(filename)[1]
        temp_path = os.path.join(self.temp_dir, f"{file_key}{file_extension}")

        with open(temp_path, 'wb') as f:
            f.write(file_content)

        return file_key

    def read_file(self, file_key: str) -> pd.DataFrame:
        """
        Read temp file and convert to DataFrame

        Args:
            file_key: Unique file identifier

        Returns:
            DataFrame with file contents
        """
        # Find file with this key
        temp_files = [f for f in os.listdir(self.temp_dir) if f.startswith(file_key)]
        if not temp_files:
            raise FileNotFoundError(f"File with key {file_key} not found")

        file_path = os.path.join(self.temp_dir, temp_files[0])
        file_extension = os.path.splitext(temp_files[0])[1].lower()

        # Read based on file type
        if file_extension == '.csv':
            # Try different encodings
            for encoding in ['utf-8', 'latin-1', 'iso-8859-1', 'cp1252']:
                try:
                    df = pd.read_csv(file_path, encoding=encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                df = pd.read_csv(file_path, encoding='utf-8', errors='ignore')

        elif file_extension in ['.xlsx', '.xls']:
            df = pd.read_excel(file_path)

        else:
            raise ValueError(f"Unsupported file type: {file_extension}")

        # Clean column names (strip spaces, lowercase)
        df.columns = [col.strip() for col in df.columns]

        return df

    def suggest_column_mapping(self, columns: List[str]) -> Dict[str, str]:
        """
        Auto-suggest column mappings using fuzzy matching

        Args:
            columns: List of column headers from file

        Returns:
            Dictionary mapping file columns to prospect fields
        """
        mappings = {}
        normalized_columns = [col.lower().strip() for col in columns]

        for prospect_field, patterns in self.FIELD_PATTERNS.items():
            best_match = None
            best_score = 0.0

            for i, col in enumerate(normalized_columns):
                for pattern in patterns:
                    # Exact match
                    if col == pattern:
                        best_match = columns[i]
                        best_score = 1.0
                        break

                    # Fuzzy match
                    score = SequenceMatcher(None, col, pattern).ratio()
                    if score > best_score and score > 0.7:  # Threshold for fuzzy matching
                        best_match = columns[i]
                        best_score = score

                if best_score == 1.0:
                    break

            if best_match:
                mappings[best_match] = prospect_field

        return mappings

    def clean_phone(self, phone: any) -> Optional[str]:
        """Clean and normalize phone number"""
        if pd.isna(phone) or phone is None:
            return None

        phone_str = str(phone).strip()

        # Remove all non-digit characters except +
        phone_clean = re.sub(r'[^\d+]', '', phone_str)

        # Remove leading zeros if more than 10 digits
        if len(phone_clean) > 10 and phone_clean.startswith('0'):
            phone_clean = phone_clean.lstrip('0')

        return phone_clean if phone_clean else None

    def clean_email(self, email: any) -> Optional[str]:
        """Clean and validate email"""
        if pd.isna(email) or email is None:
            return None

        email_str = str(email).strip().lower()

        try:
            validate_email(email_str)
            return email_str
        except EmailNotValidError:
            return None

    def parse_currency(self, value: any) -> Optional[float]:
        """Parse currency value"""
        if pd.isna(value) or value is None:
            return None

        if isinstance(value, (int, float)):
            return float(value)

        # Remove currency symbols and commas
        value_str = str(value).strip()
        value_str = re.sub(r'[₹$,\s]', '', value_str)

        try:
            return float(value_str)
        except ValueError:
            return None

    def parse_tags(self, tags: any) -> Optional[List[str]]:
        """Parse tags from various formats"""
        if pd.isna(tags) or tags is None:
            return None

        tags_str = str(tags).strip()

        # Split by comma, semicolon, or pipe
        tag_list = re.split(r'[,;|]', tags_str)
        tag_list = [t.strip() for t in tag_list if t.strip()]

        return tag_list if tag_list else None

    def validate_row(self, row_data: Dict, row_number: int,
                    existing_emails: set, existing_phones: set) -> Tuple[bool, List[str], List[str], bool, Optional[Dict]]:
        """
        Validate a single row

        Returns:
            (is_valid, errors, warnings, is_duplicate, duplicate_info)
        """
        errors = []
        warnings = []
        is_duplicate = False
        duplicate_info = None

        # Check required fields (at least one of name, email, or phone)
        if not (row_data.get('full_name') or row_data.get('email') or row_data.get('phone')):
            errors.append("Row must have at least name, email, or phone")

        # Validate email format
        email = row_data.get('email')
        if email:
            try:
                validate_email(email)
            except EmailNotValidError:
                errors.append(f"Invalid email format: {email}")

        # Check for duplicates
        if email and email in existing_emails:
            is_duplicate = True
            duplicate_info = {"field": "email", "value": email}
            warnings.append(f"Duplicate email found: {email}")

        if row_data.get('phone') and row_data.get('phone') in existing_phones:
            if not is_duplicate:  # Only set if not already duplicate by email
                is_duplicate = True
                duplicate_info = {"field": "phone", "value": row_data.get('phone')}
            warnings.append(f"Duplicate phone found: {row_data.get('phone')}")

        # Validate estimated value is positive
        if row_data.get('estimated_portfolio_value') is not None:
            if row_data['estimated_portfolio_value'] < 0:
                errors.append("Estimated portfolio value cannot be negative")

        is_valid = len(errors) == 0

        return is_valid, errors, warnings, is_duplicate, duplicate_info

    def preview_import(self, file_key: str, column_mappings: Dict[str, str],
                      existing_emails: set, existing_phones: set,
                      preview_rows: int = 10) -> Dict:
        """
        Preview import with validation

        Args:
            file_key: Unique file identifier
            column_mappings: Dictionary mapping file columns to prospect fields
            existing_emails: Set of existing prospect emails
            existing_phones: Set of existing prospect phones
            preview_rows: Number of rows to preview

        Returns:
            Dictionary with preview data and validation results
        """
        df = self.read_file(file_key)

        total_rows = len(df)
        valid_rows = 0
        invalid_rows = 0

        preview_data = []

        # Process preview rows
        for idx, row in df.head(preview_rows).iterrows():
            row_data = {}

            # Map columns according to mappings
            for file_col, prospect_field in column_mappings.items():
                if file_col in df.columns:
                    value = row[file_col]

                    # Clean data based on field type
                    if prospect_field == 'email':
                        row_data[prospect_field] = self.clean_email(value)
                    elif prospect_field in ['phone', 'alternate_phone']:
                        row_data[prospect_field] = self.clean_phone(value)
                    elif prospect_field == 'estimated_portfolio_value':
                        row_data[prospect_field] = self.parse_currency(value)
                    elif prospect_field == 'tags':
                        row_data[prospect_field] = self.parse_tags(value)
                    elif prospect_field == 'full_name':
                        row_data[prospect_field] = str(value).strip() if not pd.isna(value) else None
                    else:
                        row_data[prospect_field] = str(value).strip() if not pd.isna(value) and value else None

            # Store unmapped columns in custom_fields
            custom_fields = {}
            for col in df.columns:
                if col not in column_mappings:
                    val = row[col]
                    if not pd.isna(val) and val:
                        custom_fields[col] = str(val)

            if custom_fields:
                row_data['custom_fields'] = custom_fields

            # Validate row
            is_valid, errors, warnings, is_duplicate, duplicate_info = self.validate_row(
                row_data, idx + 1, existing_emails, existing_phones
            )

            if is_valid:
                valid_rows += 1
            else:
                invalid_rows += 1

            preview_data.append({
                "row_number": idx + 1,
                "data": row_data,
                "is_valid": is_valid,
                "errors": errors,
                "warnings": warnings,
                "is_duplicate": is_duplicate,
                "duplicate_info": duplicate_info
            })

        return {
            "file_key": file_key,
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "preview_rows": preview_data
        }

    def process_import(self, file_key: str, column_mappings: Dict[str, str],
                      existing_emails: set, existing_phones: set,
                      skip_duplicates: bool = True) -> Tuple[List[Dict], List[Dict]]:
        """
        Process full import

        Args:
            file_key: Unique file identifier
            column_mappings: Dictionary mapping file columns to prospect fields
            existing_emails: Set of existing prospect emails
            existing_phones: Set of existing prospect phones
            skip_duplicates: Whether to skip duplicate records

        Returns:
            Tuple of (successful_records, failed_records)
        """
        df = self.read_file(file_key)

        successful_records = []
        failed_records = []

        for idx, row in df.iterrows():
            row_data = {}

            # Map columns according to mappings
            for file_col, prospect_field in column_mappings.items():
                if file_col in df.columns:
                    value = row[file_col]

                    # Clean data based on field type
                    if prospect_field == 'email':
                        row_data[prospect_field] = self.clean_email(value)
                    elif prospect_field in ['phone', 'alternate_phone']:
                        row_data[prospect_field] = self.clean_phone(value)
                    elif prospect_field == 'estimated_portfolio_value':
                        row_data[prospect_field] = self.parse_currency(value)
                    elif prospect_field == 'tags':
                        row_data[prospect_field] = self.parse_tags(value)
                    elif prospect_field == 'full_name':
                        row_data[prospect_field] = str(value).strip() if not pd.isna(value) else None
                    else:
                        row_data[prospect_field] = str(value).strip() if not pd.isna(value) and value else None

            # Store unmapped columns in custom_fields
            custom_fields = {}
            for col in df.columns:
                if col not in column_mappings:
                    val = row[col]
                    if not pd.isna(val) and val:
                        custom_fields[col] = str(val)

            if custom_fields:
                row_data['custom_fields'] = custom_fields

            # Validate row
            is_valid, errors, warnings, is_duplicate, duplicate_info = self.validate_row(
                row_data, idx + 1, existing_emails, existing_phones
            )

            # Skip if duplicate and skip_duplicates is True
            if skip_duplicates and is_duplicate:
                failed_records.append({
                    "row_number": idx + 1,
                    "data": row_data,
                    "errors": ["Duplicate record skipped"] + errors,
                    "warnings": warnings
                })
                continue

            if is_valid:
                successful_records.append(row_data)
                # Add to existing sets to prevent duplicates within the import file
                if row_data.get('email'):
                    existing_emails.add(row_data['email'])
                if row_data.get('phone'):
                    existing_phones.add(row_data['phone'])
            else:
                failed_records.append({
                    "row_number": idx + 1,
                    "data": row_data,
                    "errors": errors,
                    "warnings": warnings
                })

        return successful_records, failed_records

    def cleanup_temp_file(self, file_key: str):
        """Delete temporary file"""
        temp_files = [f for f in os.listdir(self.temp_dir) if f.startswith(file_key)]
        for temp_file in temp_files:
            os.remove(os.path.join(self.temp_dir, temp_file))
