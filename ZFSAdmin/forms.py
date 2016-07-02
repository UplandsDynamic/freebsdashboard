from django import forms
from django.core.validators import MaxLengthValidator
from .validators import validate_filesystem_value


class FileSystemSelection(forms.Form):
    filesystems = forms.MultipleChoiceField(widget=forms.CheckboxSelectMultiple)

    def __init__(self, *args, **kwargs):
        choices = kwargs.pop('choices', None)
        super(FileSystemSelection, self).__init__(*args, **kwargs)
        self.fields['filesystems'].choices = choices


class NewFileSystem(forms.Form):
    datasets = forms.ChoiceField(widget=forms.Select)
    # filesystem = forms.Textarea(widget=forms.Textarea, validators=[MaxLengthValidator(250)])
    filesystem = forms.CharField(widget=forms.TextInput(attrs={'size': 30}),
                                 max_length=255,
                                 help_text='255 characters max.',
                                 validators=[validate_filesystem_value],
                                 required=False)
    compression = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    sharenfs = forms.BooleanField(widget=forms.CheckboxInput, required=False)
    quota = forms.IntegerField(widget=forms.TextInput(attrs={'required': False, 'size': 5}), initial=0)

    def __init__(self, *args, **kwargs):
        dataset_choices = kwargs.pop('choices', None)
        dataset_initial_value = kwargs.pop('initial', None)
        compression_choice = kwargs.pop('compression', True)
        sharenfs_choice = kwargs.pop('sharenfs', False)
        super(NewFileSystem, self).__init__(*args, **kwargs)
        # labels
        self.fields['filesystem'].label = "Enter filsystem name"
        self.fields['datasets'].label = "Select Dataset"
        self.fields['compression'].label = "Use compression"
        self.fields['sharenfs'].label = "Share with NFS"
        self.fields['quota'].label = "File system quota (0 is unlimited)"
        # choice setup
        self.fields['datasets'].choices = dataset_choices
        self.fields['datasets'].initial = dataset_initial_value
        self.fields['compression'].initial = compression_choice
        self.fields['sharenfs'].initial = sharenfs_choice

