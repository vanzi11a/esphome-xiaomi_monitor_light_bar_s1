#!/usr/bin/env python3
"""
Xiaomi Monitor Light Bar Preset Generator

This script generates ESPHome configuration for custom light presets.
Users define their presets in a JSON file and this script creates the
corresponding ESPHome YAML configuration with button entities.

Usage:
    python scripts/generate_presets.py [preset_file]

If no preset file is specified, it looks for 'presets.json' in the current directory.
"""

import json
import argparse
import sys
from pathlib import Path
from typing import List, Dict, Any

try:
    import yaml
except ImportError:
    print("Warning: PyYAML not installed. Install with: pip install pyyaml")
    print("Falling back to basic YAML generation...")
    yaml = None


def load_presets(preset_file: Path) -> List[Dict[str, Any]]:
    """Load preset definitions from JSON file."""
    try:
        with open(preset_file, 'r') as f:
            data = json.load(f)
        
        # Validate the structure
        if not isinstance(data, dict) or 'presets' not in data:
            raise ValueError("JSON file must contain a 'presets' array")
        
        presets = data['presets']
        if not isinstance(presets, list):
            raise ValueError("'presets' must be an array")
        
        # Validate each preset
        for i, preset in enumerate(presets):
            required_fields = ['name', 'temperature', 'brightness']
            for field in required_fields:
                if field not in preset:
                    raise ValueError(f"Preset {i} missing required field: {field}")
            
            # Validate ranges
            temp = preset['temperature']
            brightness = preset['brightness']
            
            if not isinstance(temp, int) or temp < 2200 or temp > 6500:
                raise ValueError(f"Preset '{preset['name']}': temperature must be integer between 2200-6500K")
            
            if not isinstance(brightness, (int, float)) or brightness < 0.1 or brightness > 1.0:
                raise ValueError(f"Preset '{preset['name']}': brightness must be number between 0.1-1.0")
        
        return presets
    
    except FileNotFoundError:
        print(f"Error: Preset file '{preset_file}' not found")
        sys.exit(1)
    except json.JSONDecodeError as e:
        print(f"Error: Invalid JSON in '{preset_file}': {e}")
        sys.exit(1)
    except ValueError as e:
        print(f"Error: {e}")
        sys.exit(1)


def generate_preset_buttons(presets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate ESPHome button configuration for presets."""
    config = {
        'globals': [{
            'id': 'preset_cycle_index',
            'type': 'int',
            'restore_value': True,
            'initial_value': '0'
        }],
        'button': []
    }
    
    for i, preset in enumerate(presets):
        button = {
            'platform': 'template',
            'name': f"{preset['name']} Preset",
            'on_press': [{
                'lambda': f'id(preset_cycle_index) = {i};'
            }, {
                'lambda': f'auto call = id(light1).turn_on(); call.set_transition_length(${{default_transition}}); float t = 1000000.0f / {preset["temperature"]}; call.set_color_temperature(t); call.set_brightness({preset["brightness"]}); call.perform();'
            }]
        }
        
        # Add icon if provided
        if 'icon' in preset:
            button['icon'] = preset['icon']
        
        config['button'].append(button)
    
    # Generate lambda code for cycling through presets
    cycle_lambda = "int current = id(preset_cycle_index);\n"
    cycle_lambda += f"int next = (current + 1) % {len(presets)};\n"
    cycle_lambda += "id(preset_cycle_index) = next;\n\n"
    cycle_lambda += "auto call = id(light1).turn_on();\n"
    cycle_lambda += "call.set_transition_length(${default_transition});\n"
    cycle_lambda += "float t = 0.0f;\n\n"
    cycle_lambda += "switch(next) {\n"
    
    for i, preset in enumerate(presets):
        cycle_lambda += f"  case {i}:\n"
        cycle_lambda += f"    t = 1000000.0f / {preset['temperature']};\n"
        cycle_lambda += f"    call.set_color_temperature(t);\n"
        cycle_lambda += f"    call.set_brightness({preset['brightness']});\n"
        cycle_lambda += f"    break;\n"
    
    cycle_lambda += "}\n"
    cycle_lambda += "call.perform();"
    
    # Add BLE dimmer override for long-press cycling
    config['sensor'] = [{
        'platform': 'miot_ylkg0xyl',
        'mac_address': '${dimmer_mac_address}',
        'bindkey': '${dimmer_bindkey}',
        'product_id': '0x15CE',
        'on_long_press': [{
            'then': [{
                'logger.log': 'knob was long pressed - cycling custom presets'
            }, {
                'lambda': f'{cycle_lambda}'
            }]
        }]
    }]
    
    return config


def generate_select_component(presets: List[Dict[str, Any]]) -> Dict[str, Any]:
    """Generate an alternative select component for presets (similar to original)."""
    options = [preset['name'] for preset in presets]
    
    # Create the lambda code for the on_value action
    lambda_code = "auto call = id(light1).turn_on();\n"
    lambda_code += "call.set_transition_length(${default_transition});\n"
    lambda_code += "float t = 0.0f;\n\n"
    lambda_code += "switch(i) {\n"
    
    for i, preset in enumerate(presets):
        lambda_code += f"  case {i}:\n"
        lambda_code += f"    t = 1000000.0f / {preset['temperature']};\n"
        lambda_code += f"    call.set_color_temperature(t);\n"
        lambda_code += f"    call.set_brightness({preset['brightness']});\n"
        lambda_code += f"    break;\n"
    
    lambda_code += "}\n"
    lambda_code += "call.perform();"
    
    select_config = {
        'select': [{
            'platform': 'template',
            'name': 'Light Presets',
            'id': 'light_presets',
            'options': options,
            'optimistic': True,
            'on_value': [{
                'then': [{
                    'lambda': f'{lambda_code}'
                }]
            }]
        }],
        # Override BLE dimmer long-press to cycle through custom presets
        'sensor': [{
            'platform': 'miot_ylkg0xyl',
            'mac_address': '${dimmer_mac_address}',
            'bindkey': '${dimmer_bindkey}',
            'product_id': '0x15CE',
            'on_long_press': [{
                'then': [{
                    'logger.log': 'knob was long pressed - cycling custom presets'
                }, {
                    'select.next': {
                        'id': 'light_presets',
                        'cycle': True
                    }
                }]
            }]
        }]
    }
    
    return select_config


def create_example_preset_file(output_path: Path):
    """Create an example preset configuration file."""
    example_config = {
        "presets": [
            {
                "name": "Office",
                "description": "Bright cool white for work",
                "temperature": 4500,
                "brightness": 1.0,
                "icon": "mdi:office-building"
            },
            {
                "name": "Reading", 
                "description": "Bright cool white for reading",
                "temperature": 5000,
                "brightness": 1.0,
                "icon": "mdi:book-open-variant"
            },
            {
                "name": "Gaming",
                "description": "Medium warm light for gaming",
                "temperature": 3000,
                "brightness": 0.7,
                "icon": "mdi:gamepad-variant"
            },
            {
                "name": "Night",
                "description": "Dim warm light for nighttime",
                "temperature": 2200,
                "brightness": 0.1,
                "icon": "mdi:weather-night"
            }
        ]
    }
    
    with open(output_path, 'w') as f:
        json.dump(example_config, f, indent=2)
    
    print(f"Created example preset file: {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Generate ESPHome presets configuration")
    parser.add_argument('preset_file', nargs='?', default='presets.json',
                        help='JSON file containing preset definitions (default: presets.json)')
    parser.add_argument('--output-dir', default='packages',
                        help='Output directory for generated files (default: packages)')
    parser.add_argument('--create-example', action='store_true',
                        help='Create an example presets.json file')
    parser.add_argument('--style', choices=['buttons', 'select'], default='buttons',
                        help='Generate style: buttons (default) or select component')
    
    args = parser.parse_args()
    
    # Create example file if requested
    if args.create_example:
        create_example_preset_file(Path('presets.example.json'))
        return
    
    preset_file = Path(args.preset_file)
    output_dir = Path(args.output_dir)
    
    # Ensure output directory exists
    output_dir.mkdir(exist_ok=True)
    
    # Load and validate presets
    presets = load_presets(preset_file)
    
    print(f"Loaded {len(presets)} presets from {preset_file}")
    
    # Generate configuration based on style
    if args.style == 'buttons':
        config = generate_preset_buttons(presets)
        output_file = output_dir / 'generated-preset-buttons.yaml'
        print("Generating preset buttons...")
    else:
        config = generate_select_component(presets)
        output_file = output_dir / 'generated-preset-select.yaml'
        print("Generating preset select component...")
    
    # Add header comment
    header = f"""# Generated preset configuration
# Created from: {preset_file}
# Style: {args.style}
# Presets: {', '.join([p['name'] for p in presets])}
# 
# To regenerate, run:
# python scripts/generate_presets.py {preset_file} --style {args.style}

"""
    
    # Write the configuration
    with open(output_file, 'w') as f:
        f.write(header)
        yaml.dump(config, f, default_flow_style=False, sort_keys=False)
    
    print(f"Generated ESPHome configuration: {output_file}")
    print(f"\nTo use, add this to your main configuration:")
    print(f"packages:")
    print(f"  - !include packages/core.yaml")
    print(f"  - !include {output_file}")
    
    # Print preset summary
    print(f"\nPreset Summary:")
    for preset in presets:
        print(f"  {preset['name']}: {preset['temperature']}K, {preset['brightness']*100:.0f}% brightness")


if __name__ == '__main__':
    main()