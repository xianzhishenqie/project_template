import os

from django.conf import settings


def get_obj(pk_or_obj, model):
    if not pk_or_obj:
        return None

    if isinstance(pk_or_obj, model):
        obj = pk_or_obj
    else:
        obj = model.objects.get(pk=pk_or_obj)

    return obj


def clear_nouse_field_file(using_queryset, file_field_name):
    file_dir_name = getattr(using_queryset.model, file_field_name).field.get_directory_name()
    file_dir = os.path.join(settings.MEDIA_ROOT, file_dir_name)
    if not os.path.exists(file_dir):
        return

    all_filenames = os.listdir(file_dir)
    using_filenames = []
    for instance in using_queryset:
        instance_file = getattr(instance, file_field_name)
        if instance_file:
            using_filenames.append(os.path.basename(instance_file.name))

    nouse_filenames = list(set(all_filenames) - set(using_filenames))
    for filename in nouse_filenames:
        file_path = os.path.join(file_dir, filename)
        os.remove(file_path)
        print('remove file: %s' % file_path)
