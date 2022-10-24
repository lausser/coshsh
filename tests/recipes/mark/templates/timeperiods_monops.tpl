{% for timeperiod in application.timeperiods %}
define timeperiod {
    timeperiod_name {{ timeperiod.name }}
    alias {{ timeperiod.alias }}
}
 
{% endfor %}

