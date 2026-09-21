from django import forms

from .models import Order


# =========================================================
# CUSTOMER ONLINE ORDER FORM
# =========================================================

class CustomerOrderForm(forms.ModelForm):

    class Meta:
        model = Order

        fields = [
            "customer_name",
            "whatsapp_number",
            "order_type",
            "notes",
        ]

        widgets = {

            "customer_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Your name",
                }
            ),

            "whatsapp_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "WhatsApp or contact number",
                }
            ),

            "order_type": forms.RadioSelect(),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Any special instructions?",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        kwargs.pop("shop", None)

        super().__init__(
            *args,
            **kwargs
        )

        self.fields[
            "whatsapp_number"
        ].required = True


# =========================================================
# STAFF COUNTER ORDER FORM
# =========================================================

class CounterOrderForm(forms.ModelForm):

    class Meta:
        model = Order

        fields = [
            "customer_name",
            "whatsapp_number",
            "notes",
        ]

        widgets = {

            "customer_name": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Customer name",
                    "autocomplete": "off",
                }
            ),

            "whatsapp_number": forms.TextInput(
                attrs={
                    "class": "form-control",
                    "placeholder": "Customer WhatsApp number",
                    "autocomplete": "off",
                }
            ),

            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 3,
                    "placeholder": "Special instructions (optional)",
                }
            ),
        }

    def __init__(self, *args, **kwargs):

        super().__init__(
            *args,
            **kwargs
        )

        # Counter orders require a customer name
        # and number so the business can send the
        # Ready for Collection notification.
        self.fields[
            "customer_name"
        ].required = True

        self.fields[
            "whatsapp_number"
        ].required = True