{% for fs in application.filesystems %}
[CheckMyDriveSize{{ fs.path }}]=C:\NSClient++\scripts\check_disk -w {{ fs.warning }} -c {{ fs.critical }}
{% endfor %}
