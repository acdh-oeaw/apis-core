from django.db import models
from django.urls import reverse
from browsing.browsing_utils import model_to_dict


class ProjectInst(models.Model):
    """ A class describing Institutions involved in the Project"""
    name = models.CharField(
        max_length=300, blank=True,
        verbose_name="Name"
        )
    abbr = models.CharField(
        max_length=300, blank=True,
        verbose_name="Abbreviation"
        )
    description = models.TextField(
        blank=True,
        verbose_name="Short description of the Institution"
        )
    website = models.URLField(
        max_length=300, blank=True,
        verbose_name="Link to the Institution's website"
        )
    logo_url = models.URLField(
        max_length=300, blank=True,
        verbose_name="Link to the Insitution's Logo",
        )
    norm_url = models.URLField(
        max_length=300, blank=True,
        verbose_name="Norm Data URL (OCRID, GND, VIAF, ...)",
        help_text="URL to any normdata record of the institution"
        )

    class Meta:

        ordering = [
            'name',
        ]
        verbose_name = "Institution involved in the Project"

    def __str__(self):
        return "{}".format(self.name)

    def field_dict(self):
        return model_to_dict(self)

    @classmethod
    def get_listview_url(self):
        return reverse('info:projectinst_browse')

    @classmethod
    def get_createview_url(self):
        return reverse('info:projectinst_create')

    def get_absolute_url(self):
        return reverse('info:projectinst_detail', kwargs={'pk': self.id})

    def get_delete_url(self):
        return reverse('info:projectinst_delete', kwargs={'pk': self.id})

    def get_edit_url(self):
        return reverse('info:projectinst_edit', kwargs={'pk': self.id})

    def get_next(self):
        next = self.__class__.objects.filter(id__gt=self.id)
        if next:
            return reverse(
                'info:projectinst_detail',
                kwargs={'pk': next.first().id}
            )
        return False

    def get_prev(self):
        prev = self.__class__.objects.filter(id__lt=self.id).order_by('-id')
        if prev:
            return reverse(
                'info:projectinst_detail',
                kwargs={'pk': prev.first().id}
            )
        return False


class TeamMember(models.Model):
    """ A class describing project's team member"""
    name = models.CharField(
        max_length=300, blank=True,
        verbose_name="Name"
        )
    description = models.TextField(
        blank=True,
        verbose_name="Short description of the Person"
        )
    website = models.URLField(
        max_length=300, blank=True,
        verbose_name="Link to the person's website"
        )
    role = models.CharField(
        max_length=300, blank=True,
        verbose_name="The person's role in the project",
        help_text="will be used to group the team member"
        )
    norm_url = models.URLField(
        max_length=300, blank=True,
        verbose_name="Norm Data URL (OCRID, GND, VIAF, ...)",
        help_text="URL to any normdata record of the person"
        )

    class Meta:

        ordering = [
            'role',
            'name',
        ]
        verbose_name = "Team Member"

    def __str__(self):
        return "{}".format(self.name)

    def field_dict(self):
        return model_to_dict(self)

    @classmethod
    def get_listview_url(self):
        return reverse('info:teammember_browse')

    @classmethod
    def get_createview_url(self):
        return reverse('info:teammember_create')

    def get_absolute_url(self):
        return reverse('info:teammember_detail', kwargs={'pk': self.id})

    def get_delete_url(self):
        return reverse('info:teammember_delete', kwargs={'pk': self.id})

    def get_edit_url(self):
        return reverse('info:teammember_edit', kwargs={'pk': self.id})

    def get_next(self):
        next = self.__class__.objects.filter(id__gt=self.id)
        if next:
            return reverse(
                'info:teammember_detail',
                kwargs={'pk': next.first().id}
            )
        return False

    def get_prev(self):
        prev = self.__class__.objects.filter(id__lt=self.id).order_by('-id')
        if prev:
            return reverse(
                'info:teammember_detail',
                kwargs={'pk': prev.first().id}
            )
        return False


class AboutTheProject(models.Model):
    """ A class containing a lengthy project description """
    title = models.CharField(
        max_length=300, blank=True,
        verbose_name="Project's Title"
        )
    subtitle = models.CharField(
        max_length=300, blank=True,
        verbose_name="Project's Sub Title"
        )
    description = models.TextField(
        blank=True,
        verbose_name="Project Description"
        )
    author = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Authors",
        help_text="The names of the Agents responsible for this description",
    )
    github = models.CharField(
        max_length=250,
        blank=True,
        verbose_name="Code Repo",
        help_text="Link to the application's source code",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:

        ordering = [
            'id',
        ]
        verbose_name = "About the Project"

    def __str__(self):
        return "{}".format(self.title)

    def field_dict(self):
        return model_to_dict(self)

    @classmethod
    def get_listview_url(self):
        return reverse('info:about_browse')

    @classmethod
    def get_createview_url(self):
        return reverse('info:about_create')

    def get_absolute_url(self):
        return reverse('info:about_detail', kwargs={'pk': self.id})

    def get_delete_url(self):
        return reverse('info:about_delete', kwargs={'pk': self.id})

    def get_edit_url(self):
        return reverse('info:about_edit', kwargs={'pk': self.id})

    def get_next(self):
        next = self.__class__.objects.filter(id__gt=self.id)
        if next:
            return reverse(
                'info:about_detail',
                kwargs={'pk': next.first().id}
            )
        return False

    def get_prev(self):
        prev = self.__class__.objects.filter(id__lt=self.id).order_by('-id')
        if prev:
            return reverse(
                'info:about_detail',
                kwargs={'pk': prev.first().id}
            )
        return False
