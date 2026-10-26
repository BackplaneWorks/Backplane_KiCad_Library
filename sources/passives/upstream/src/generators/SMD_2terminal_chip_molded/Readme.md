# SMD 2 terminal chip molded footprint generator

Program to generate KiCad footprints using KicadModTree

Devices included:
- 2 terminal SMD chip molded

## Usage

To generate the footprints, run one of the following commands:

```
$ python3 ./ipc_2terminal_chip_molded_generator.py <file>  # builds footprints for definitions included in that file
```

## Configuration

Design parameters for each device type (for example, device dimensions) are contained in yaml files in `size_definitions` folder.

The configuration for each device is in a separate YAML file in the `size_definitions` folder.  
The document for each type has the information needed to create the footprint.

This is a script to generate series of footprints with the same name and description format.
The name of the footprints is specified in file `package_config_KLCv3.0.yaml`, for metric, non-metric and tantalum capacitors:

```
fp_name_format_string: '{prefix:s}_{code_imperial:s}_{code_metric:s}Metric{suffix:s}'
fp_name_non_metric_format_string: '{prefix:s}_{code_imperial:s}{suffix:s}'
fp_name_tantal_format_string: '{prefix:s}_EIA-{code_metric:s}_{code_letter:s}{suffix:s}'
```
Each series of devices are specified in `part_definitions.yaml`file, with common values for all the device in the series. For example:
```
resistor:
    fp_lib_name: 'Resistor_SMD'  # Library name
    size_definitions: ['resistor_chip.yaml', 'resistor_chip_smaller_0603.yaml', 'resistor_chip_wide_body.yaml']  # YAML definitions file
    ipc_reference: "ipc_spec_larger_or_equal_0603"  # IPC rules to use when creating the footprint
    prefix: 'R' 
    description: 'Resistor SMD {code_imperial:s} ({code_metric:s} Metric), square (rectangular) end terminal, IPC-7351 nominal, {size_info:s}' # Description format for all the series. Each {variable} will be replaced by its specified value.
    keywords: 'resistor'
    ipc_density: 'nominal'
    pad_length_addition: 0
    suffix: ""
```

These strings are combined with the device-specific values and keywords (see below) and are included in the YAML file. 

## YAML file

```
footprint_series_name:
```
Then, imperial and metric package names and code letter (for tantalum capacitors) are specified.
For resistors and capacitors, for example, only metric and imperial codes are defined:
```
    code_imperial: "0603"
    code_metric: "1608"
```

Tantalum capacitors are usually defined by metric and letter code:
```
    code_metric: '1608-08'
    code_letter: 'AVX-J' # This is only used for tantalum capacitors

```

The next part of the configuration file is about the phyical device that sits on the footprint, defining the size of the body and terminals.

```
    body_length:
        minimum: 1.45
        maximum: 1.75
    body_width:
        minimum: 0.65
        maximum: 0.95
    terminal_length:
        minimum: 0.2
        maximum: 0.5
```

The next part an explanation of the source of those dimensions:

```
    size_info: '(Body size source: IPC-SM-782 page 76, https://www.pcb-3d.com/wordpress/wp-content/uploads/ipc-sm-782a_amendment_1_and_2.pdf)'
```

The footprint name and description of the Kicad footprint will be a combination of `code_imperial`, `code_metric`, `code_letter` and `size_info` strings, using the string format provided in the configuration file (see above).

If a keyword `custom_name` exists with a string value, it is used as the footprint name, and the description will be read from the `description` keyword:
```
    custom_name: 'AVX_custom_package'
    description: 'This is the description of the AVX custom package'
```


