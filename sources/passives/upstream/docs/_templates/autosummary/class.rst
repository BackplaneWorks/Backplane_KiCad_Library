{{ fullname.split('.')[-1] | escape | underline}}

.. currentmodule:: {{ module }}

.. autoclass:: {{ module }}.{{ objname }}
   :members:
   :show-inheritance:
   :inherited-members:

   .. inheritance-diagram:: {{ fullname }}
      :parts: 1

   {% block methods %}

   {% if methods %}
   .. rubric:: {{ _('Methods') }}

   .. autosummary::
   {% for item in methods %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   {% block attributes %}
   {% if attributes %}
   .. rubric:: {{ _('Attributes') }}

   .. autosummary::
   {% for item in attributes %}
      ~{{ name }}.{{ item }}
   {%- endfor %}
   {% endif %}
   {% endblock %}

   .. automethod:: __init__
