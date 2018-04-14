from . import models
from .models import deepest_instance
from import_export.fields import Field
from import_export.resources import ModelResource
from import_export.admin import ImportExportModelAdmin
from django.contrib import admin

class SupersenseResource(ModelResource):
    name = Field()
    article_md = Field()
    article_modified = Field()
    animacy = Field()
    parent = Field()

    class Meta:
        model = models.Supersense

    def dehydrate_name(self, supersense):
        return deepest_instance(supersense.current_revision).name

    def dehydrate_article_md(self, supersense):
        return deepest_instance(supersense.current_revision).article_revision.content

    def dehydrate_article_modified(self, supersense):
        return deepest_instance(supersense.current_revision).article_revision.modified

    def dehydrate_animacy(self, supersense):
        return deepest_instance(supersense.current_revision).animacy

    def dehydrate_parent(self, supersense):
        return deepest_instance(supersense.current_revision).parent

class SupersenseAdmin(ImportExportModelAdmin):
    resource_class = SupersenseResource

admin.site.register(models.Supersense, SupersenseAdmin)
#admin.site.register(Supersense)
admin.site.register(models.SupersenseRevision)
admin.site.register(models.Construal)
admin.site.register(models.Language)
admin.site.register(models.Corpus)
admin.site.register(models.Adposition)
admin.site.register(models.AdpositionRevision)
admin.site.register(models.Usage)
admin.site.register(models.UsageRevision)
admin.site.register(models.Example)
admin.site.register(models.ExampleRevision)
