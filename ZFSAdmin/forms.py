from django import forms
from django.core.validators import MaxLengthValidator


class FileSystemSelection(forms.Form):
	filesystems = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

	def __init__(self, *args, **kwargs):
		choices = kwargs.pop('choices', None)
		super(FileSystemSelection, self).__init__(*args, **kwargs)
		self.fields['filesystems'].choices = choices


class NewFileSystem(forms.Form):
	datasets = forms.ChoiceField(widget=forms.RadioSelect)
	filesystems = forms.CharField(widget=forms.Textarea, validators=[MaxLengthValidator(250)])

	def __init__(self, *args, **kwargs):
		choices = kwargs.pop('choices', None)
		initial = kwargs.pop('initial', None)
		super(NewFileSystem, self).__init__(*args, **kwargs)
		self.fields['filesystems'].label = "Select File Systems"
		self.fields['datasets'].label = "Select Dataset"
		self.fields['datasets'].choices = choices
		self.fields['datasets'].initial = initial