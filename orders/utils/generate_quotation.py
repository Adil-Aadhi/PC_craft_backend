from io import BytesIO
from django.core.files.base import ContentFile
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas


def generate_quotation_pdf(order):

    # prevent regenerating
    if order.quotation_pdf:
        return order.quotation_pdf.url

    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)

    # Header
    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, 800, "PC Build Quotation")

    c.setFont("Helvetica", 10)
    c.drawString(50, 780, f"Order ID: ORD-{order.order_id}")
    c.drawString(50, 765, f"Customer: {order.user.username}")
    c.drawString(50, 750, f"Status: {order.status}")

    y = 720

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

    # Components Section
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Components:")
    y -= 20

    c.setFont("Helvetica", 10)

    for name, item in components:
        if item:
            c.drawString(60, y, f"{name}: {item.name} - ₹{item.price}")
            y -= 15

            if y < 100:
                c.showPage()
                y = 800

    # Compatibility info
    if hasattr(cart, "is_compatible"):
        y -= 10
        c.setFont("Helvetica-Bold", 11)
        c.drawString(50, y, "Compatibility:")
        y -= 15

        c.setFont("Helvetica", 9)
        text = cart.compatibility_notes or "All components compatible"
        c.drawString(60, y, text[:90])

    # Pricing Section
    y -= 30
    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y, "Price Summary:")
    y -= 20

    # 🔹 Use values stored in Order
    components_total = order.components_total
    service_charge = order.worker_earning
    platform_fee = order.platform_fee
    final_total = order.total_price

    c.setFont("Helvetica", 10)

    c.drawString(60, y, f"Components Total: ₹{components_total}")
    y -= 15

    c.drawString(60, y, f"Assembly & Service Charge: ₹{service_charge}")
    y -= 15

    c.drawString(60, y, f"Platform Fee: ₹{platform_fee}")
    y -= 20

    c.setFont("Helvetica-Bold", 13)
    c.drawString(50, y, f"Final Amount: ₹{final_total}")

    c.save()
    buffer.seek(0)

    file_name = f"quotation_{order.order_id}.pdf"

    order.quotation_pdf.save(
        file_name,
        ContentFile(buffer.read()),
        save=True
    )

    return order.quotation_pdf.url