from django import forms


class DatasetSelection(forms.Form):
	# Datasets = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple,
	#                                    choices=[])

	datasets = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

	def __init__(self, *args, **kwargs):
		choices = kwargs.pop('choices', None)
		super(DatasetSelection, self).__init__(*args, **kwargs)
		self.fields['datasets'].choices = choices
