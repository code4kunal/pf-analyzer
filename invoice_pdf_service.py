"""
Invoice PDF Generation Service using ReportLab
"""
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.enums import TA_LEFT, TA_RIGHT, TA_CENTER
from datetime import datetime
from pathlib import Path
import logging

logger = logging.getLogger(__name__)


class InvoicePDFGenerator:
    """Generate professional invoice PDFs"""

    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.company_name = "GrowFolio Investment Advisory"
        self.company_email = "help@grow-folio.in"
        self.company_phone = "+91 XXXXX-XXXXX"
        self.company_address = "Mumbai, Maharashtra, India"

    def generate_invoice_pdf(self, invoice, customer, output_path: str):
        """
        Generate invoice PDF

        Args:
            invoice: Invoice model instance
            customer: Customer model instance
            output_path: Path where PDF will be saved
        """
        try:
            # Create PDF document
            doc = SimpleDocTemplate(
                output_path,
                pagesize=letter,
                rightMargin=72,
                leftMargin=72,
                topMargin=72,
                bottomMargin=18
            )

            # Container for PDF elements
            story = []

            # Add header
            story.extend(self._create_header())
            story.append(Spacer(1, 0.3 * inch))

            # Add invoice details
            story.extend(self._create_invoice_info(invoice, customer))
            story.append(Spacer(1, 0.3 * inch))

            # Add line items table
            story.append(self._create_line_items_table(invoice))
            story.append(Spacer(1, 0.3 * inch))

            # Add totals
            story.append(self._create_totals_table(invoice))
            story.append(Spacer(1, 0.5 * inch))

            # Add payment info if paid
            if invoice.status.value == "PAID" and invoice.payment_date:
                story.extend(self._create_payment_info(invoice))
                story.append(Spacer(1, 0.3 * inch))

            # Add footer
            story.extend(self._create_footer())

            # Build PDF
            doc.build(story)

            logger.info(f"Invoice PDF generated: {output_path}")
            return output_path

        except Exception as e:
            logger.error(f"Error generating invoice PDF: {e}")
            raise

    def _create_header(self):
        """Create invoice header with company info"""
        elements = []

        # Company name
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#1a365d'),
            spaceAfter=12,
            alignment=TA_CENTER
        )
        elements.append(Paragraph(self.company_name, title_style))

        # Company details
        company_style = ParagraphStyle(
            'CompanyDetails',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#4a5568'),
            alignment=TA_CENTER
        )
        company_details = f"{self.company_address} | {self.company_phone} | {self.company_email}"
        elements.append(Paragraph(company_details, company_style))

        return elements

    def _create_invoice_info(self, invoice, customer):
        """Create invoice and customer information section"""
        elements = []

        # Invoice title
        invoice_title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#2d3748'),
            spaceAfter=12
        )
        elements.append(Paragraph("INVOICE", invoice_title_style))

        # Create two-column layout for invoice and customer info
        data = [
            [
                Paragraph(f"<b>Invoice Number:</b> {invoice.invoice_number}", self.styles['Normal']),
                Paragraph(f"<b>Bill To:</b>", self.styles['Normal'])
            ],
            [
                Paragraph(f"<b>Invoice Date:</b> {invoice.invoice_date.strftime('%d %B %Y')}", self.styles['Normal']),
                Paragraph(f"{customer.full_name}", self.styles['Normal'])
            ],
            [
                Paragraph(f"<b>Due Date:</b> {invoice.due_date.strftime('%d %B %Y')}", self.styles['Normal']),
                Paragraph(f"{customer.email}" if customer.email else "", self.styles['Normal'])
            ],
            [
                Paragraph(f"<b>Status:</b> <b><font color='{self._get_status_color(invoice.status.value)}'>{invoice.status.value}</font></b>", self.styles['Normal']),
                Paragraph(f"{customer.phone}" if customer.phone else "", self.styles['Normal'])
            ]
        ]

        table = Table(data, colWidths=[3 * inch, 3 * inch])
        table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 0),
        ]))

        elements.append(table)
        return elements

    def _create_line_items_table(self, invoice):
        """Create line items table"""
        # Header
        data = [
            ['Description', 'Quantity', 'Unit Price', 'Amount']
        ]

        # Add line items
        line_items = invoice.line_items or []
        if isinstance(line_items, list):
            for item in line_items:
                data.append([
                    item.get('description', ''),
                    str(item.get('quantity', 1)),
                    f"₹{item.get('unit_price', 0):,.2f}",
                    f"₹{item.get('amount', 0):,.2f}"
                ])
        else:
            # Default line item if none specified
            data.append([
                'Investment Advisory Services',
                '1',
                f"₹{invoice.subtotal:,.2f}",
                f"₹{invoice.subtotal:,.2f}"
            ])

        # Create table
        table = Table(data, colWidths=[3 * inch, 1 * inch, 1.25 * inch, 1.25 * inch])
        table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 12),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),

            # Data rows styling
            ('ALIGN', (1, 1), (-1, -1), 'RIGHT'),
            ('ALIGN', (0, 1), (0, -1), 'LEFT'),
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#f7fafc')]),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
        ]))

        return table

    def _create_totals_table(self, invoice):
        """Create totals summary table"""
        data = [
            ['Subtotal:', f"₹{invoice.subtotal:,.2f}"],
            ['Tax:', f"₹{invoice.tax_amount:,.2f}"],
            ['Total:', f"₹{invoice.total_amount:,.2f}"]
        ]

        if invoice.paid_amount > 0:
            data.append(['Paid Amount:', f"₹{invoice.paid_amount:,.2f}"])
            balance = invoice.total_amount - invoice.paid_amount
            data.append(['Balance Due:', f"₹{balance:,.2f}"])

        table = Table(data, colWidths=[4.5 * inch, 2 * inch])
        table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, -2), 'Helvetica'),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#1a365d')),
            ('LINEABOVE', (0, -1), (-1, -1), 2, colors.HexColor('#1a365d')),
            ('TOPPADDING', (0, 0), (-1, -1), 6),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ]))

        return table

    def _create_payment_info(self, invoice):
        """Create payment information section"""
        elements = []

        payment_style = ParagraphStyle(
            'PaymentInfo',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2f855a'),
            spaceAfter=4
        )

        elements.append(Paragraph(f"<b>Payment Received</b>", payment_style))
        elements.append(Paragraph(f"Date: {invoice.payment_date.strftime('%d %B %Y')}", payment_style))

        if invoice.payment_method:
            elements.append(Paragraph(f"Method: {invoice.payment_method}", payment_style))

        if invoice.payment_reference:
            elements.append(Paragraph(f"Reference: {invoice.payment_reference}", payment_style))

        return elements

    def _create_footer(self):
        """Create invoice footer"""
        elements = []

        footer_style = ParagraphStyle(
            'Footer',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor=colors.HexColor('#718096'),
            alignment=TA_CENTER
        )

        elements.append(Spacer(1, 0.5 * inch))
        elements.append(Paragraph("Thank you for your business!", footer_style))
        elements.append(Paragraph(
            "For any queries, please contact us at help@grow-folio.in",
            footer_style
        ))

        return elements

    def _get_status_color(self, status: str) -> str:
        """Get color for invoice status"""
        colors_map = {
            'DRAFT': '#718096',      # Gray
            'SENT': '#3182ce',       # Blue
            'PAID': '#2f855a',       # Green
            'OVERDUE': '#c53030',    # Red
            'CANCELLED': '#e53e3e'   # Red
        }
        return colors_map.get(status, '#718096')


# Global instance
pdf_generator = InvoicePDFGenerator()
