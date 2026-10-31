from django import forms

from .models import Share, Watch


class ShareModelForm(forms.ModelForm):
    """Инструмент"""

    class Meta:
        model = Share
        fields = "__all__"


class WatchModelForm(forms.ModelForm):
    """Наблюдение за акцией"""

    class Meta:
        model = Watch
        fields = ("share", "target_price", "direction")

    def clean_target_price(self):
        value = self.cleaned_data.get("target_price")
        if value is None or value <= 0:
            raise forms.ValidationError(
                "Целевая цена должна быть положительным числом."
            )
        return value
