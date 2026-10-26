# generators is free software: you can redistribute it and/or modify it under the terms
# of the GNU General Public License as published by the Free Software Foundation, either
# version 3 of the License, or (at your option) any later version.
#
# generators is distributed in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS FOR A
# PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# generators. If not, see < http://www.gnu.org/licenses/ >.
#
# (C) The KiCad Librarian Team

"""
Utilities for migrating old code to YAML-input
"""
import functools
import inspect
import yaml
import sys

def print_params_as_yaml(key_arg=None, file_obj=sys.stdout):
    """
    A decorator that converts the parameters of a function to YAML format and prints or writes them.

    Args:
        key_arg (str): The name of the argument that will be used as the key in the YAML dictionary, or None to use the return value
        file_obj (file-like object, optional): The file-like object to write the YAML output to. Defaults to sys.stdout.

    Returns:
        The decorated function.

    Raises:
        ValueError: If the key argument is not provided in the function call.
    """
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get the function signature
            sig = inspect.signature(func)
            # Bind the arguments to the function signature
            bound_arguments = sig.bind(*args, **kwargs)
            # Convert the bound arguments to a dictionary
            params = dict(bound_arguments.arguments)
            
            # Extract the value of the key_arg
            if key_arg not in params and key_arg is not None:
                raise ValueError(f"The key argument '{key_arg}' is not provided in the function call.")
            
            # Execute the function
            ret = func(*args, **kwargs)

            if key_arg is None:
                key_value = ret
            else: # key_arg is in the parameters
                # Some generators needs the key arg to be part of the params
                # So we leave it in there.
                key_value = params.get(key_arg)

            # If the caller provided a name_additions parameter, append them
            # underscore-separated to the key_value. Accept either a list/tuple
            # or single string values.
            na = params.get('name_additions')
            if na:
                if isinstance(na, (list, tuple)):
                    additions = [str(x) for x in na if x is not None and x != '']
                else:
                    additions = [str(na)]
                if additions:
                    key_value = f"{key_value}_{'_'.join(additions)}"
            
            # Add the function name to the parameters
            params['func'] = func.__name__
            yaml_dict = {key_value: params}
            
            # Convert the parameters dictionary to YAML format
            params_yaml = yaml.dump(yaml_dict, default_flow_style=False)
            
            # Print or write the parameters in YAML format
            file_obj.write(params_yaml)
            file_obj.write('\n\n')
        
        return wrapper
    return decorator
