from django import forms


NUMBER_CHOICES = [(str(n), str(n)) for n in range(1, 46)]


class PurchaseForm(forms.Form):
    numbers = forms.MultipleChoiceField(
        choices=NUMBER_CHOICES,
        required=False,
        widget=forms.CheckboxSelectMultiple,
    )
    quantity = forms.IntegerField(
        min_value=1,
        max_value=10,
        initial=1,
        label="매수",
    )

    def clean_numbers(self):
        raw_numbers = self.cleaned_data.get("numbers", [])
        numbers = [int(n) for n in raw_numbers]

        if len(numbers) > 6:
            raise forms.ValidationError("번호는 최대 6개까지 선택할 수 있습니다.")

        if len(set(numbers)) != len(numbers):
            raise forms.ValidationError("중복 번호는 선택할 수 없습니다.")

        if any(number < 1 or number > 45 for number in numbers):
            raise forms.ValidationError("번호는 1~45 범위여야 합니다.")

        return sorted(numbers)