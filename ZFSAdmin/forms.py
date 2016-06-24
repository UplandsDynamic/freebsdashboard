from django import forms


class FileSystemSelection(forms.Form):
	filesystems = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

	def __init__(self, *args, **kwargs):
		choices = kwargs.pop('choices', None)
		super(FileSystemSelection, self).__init__(*args, **kwargs)
		self.fields['filesystems'].choices = choices


class NewFileSystem(forms.Form):
	zpools = forms.ChoiceField(widget=forms.RadioSelect)
	filesystems = forms.CharField(widget=forms.Textarea)

	def __init__(self, *args, **kwargs):
		choices = kwargs.pop('choices', None)
		initial = kwargs.pop('initial', None)
		super(NewFileSystem, self).__init__(*args, **kwargs)
		self.fields['filesystems'].label = "Select File Systems"
		self.fields['zpools'].label = "Select Zpool"
		self.fields['zpools'].choices = choices
		self.fields['zpools'].initial = initial
