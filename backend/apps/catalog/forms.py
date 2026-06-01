from django import forms

from .models import Review


class ReviewForm(forms.ModelForm):
    class Meta:
        model = Review
        fields = ["rating", "text"]
        widgets = {
            "rating": forms.RadioSelect(choices=[(i, f"{i} ★") for i in range(1, 6)]),
            "text": forms.Textarea(attrs={
                "rows": 4,
                "maxlength": 2000,
                "placeholder": "Расскажите, что понравилось или нет",
            }),
        }
        labels = {"rating": "Оценка", "text": "Ваш отзыв"}

    def clean_rating(self):
        r = int(self.cleaned_data.get("rating") or 0)
        if not 1 <= r <= 5:
            raise forms.ValidationError("Оценка должна быть от 1 до 5.")
        return r

    def clean_text(self):
        t = (self.cleaned_data.get("text") or "").strip()
        if t and len(t) < 10:
            raise forms.ValidationError("Отзыв слишком короткий — минимум 10 символов.")
        return t
