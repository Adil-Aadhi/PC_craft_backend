from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from django.core.files.base import ContentFile
from io import BytesIO
from django.utils.timezone import localtime


def generate_invoice(order):

    buffer = BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)

    width, height = A4

    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(40, height - 50, "PC-Craft Invoice")

    p.setFont("Helvetica", 10)
    p.drawRightString(width - 40, height - 50, f"Invoice #: INV-{str(order.order_id)[:8].upper()}")
    p.drawRightString(width - 40, height - 65, f"Date: {localtime(order.created_at).strftime('%d %b %Y')}")

    # Customer Info
    p.setFont("Helvetica-Bold", 12)
    p.drawString(40, height - 100, "Bill To:")

    p.setFont("Helvetica", 10)
    p.drawString(40, height - 115, order.user.username)
    p.drawString(40, height - 130, order.user.email)

    # Payment Info
    payment = order.payments.filter(status="SUCCESS").first()

    p.drawString(40, height - 160, f"Order ID: ORD-{order.order_id}")

    if payment:
        p.drawString(40, height - 175, f"Payment ID: {payment.razorpay_payment_id}")

    # Table Header
    y = height - 210

    p.setFont("Helvetica-Bold", 11)
    p.drawString(40, y, "Component")
    p.drawString(300, y, "Price (₹)")
    p.line(40, y - 5, width - 40, y - 5)

    y -= 20
    p.setFont("Helvetica", 10)

    cart = order.cart_item

    components = [
        ("CPU", cart.cpu),
        ("Motherboard", cart.motherboard),
        ("RAM", cart.ram),
        ("GPU", cart.gpu),
        ("Storage", cart.storage),
        ("PSU", cart.psu),
        ("Case", cart.case),
        ("Cooler", cart.cooler),
        ("Case Fan", cart.case_fan),
    ]

    for name, item in components:
        if item:
            p.drawString(40, y, f"{name}: {item.name}")
            p.drawRightString(width - 40, y, f"₹{item.price}")

            y -= 18

            if y < 120:
                p.showPage()
                y = height - 60

    # Price Summary
    y -= 10
    p.line(40, y, width - 40, y)

    y -= 20
    p.setFont("Helvetica", 10)

    components_total = order.components_total
    service_charge = order.worker_earning
    platform_fee = order.platform_fee
    total_price = order.total_price

    p.drawString(40, y, "Components Total:")
    p.drawRightString(width - 40, y, f"₹{components_total}")

    y -= 18

    p.drawString(40, y, "Assembly & Service Charge:")
    p.drawRightString(width - 40, y, f"₹{service_charge}")

    y -= 18

    p.drawString(40, y, "Platform Fee:")
    p.drawRightString(width - 40, y, f"₹{platform_fee}")

    y -= 10
    p.line(40, y, width - 40, y)

    y -= 20
    p.setFont("Helvetica-Bold", 12)

    p.drawString(40, y, "Total Paid:")
    p.drawRightString(width - 40, y, f"₹{total_price}")

    # Footer
    y -= 40
    p.setFont("Helvetica", 9)

    p.drawString(40, y, "Thank you for choosing PC-Craft for your custom build.")
    p.drawString(40, y - 15, "This is a system generated invoice.")

    p.showPage()
    p.save()

    buffer.seek(0)

    return ContentFile(
        buffer.read(),
        name=f"invoice_{order.order_id}.pdf"
    )