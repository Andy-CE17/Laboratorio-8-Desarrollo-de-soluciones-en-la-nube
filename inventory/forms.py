from django import forms
from .models import Product


class ProductForm(forms.ModelForm):
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if user and not (user.is_superuser or user.role == user.Role.ADMIN):
            self.fields.pop("store")
        elif user:
            self.fields["store"].required = True

    class Meta:
        model = Product
        fields = ["code", "name", "store", "category", "description", "price", "stock"]
        widgets = {
            "code": forms.TextInput(attrs={"placeholder": "TEC-001"}),
            "name": forms.TextInput(attrs={"placeholder": "Ej. Monitor ultrawide 34 pulgadas"}),
            "description": forms.Textarea(attrs={"rows": 4, "placeholder": "Detalles útiles del producto"}),
            "price": forms.NumberInput(attrs={"min": "0", "step": "0.01", "placeholder": "0.00"}),
            "stock": forms.NumberInput(attrs={"min": "0", "step": "1", "placeholder": "0"}),
        }

    def clean_code(self):
        return self.cleaned_data["code"].strip().upper()
