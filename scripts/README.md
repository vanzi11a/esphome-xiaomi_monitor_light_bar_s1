# Preset Generator Scripts

## generate_presets.py

Python script that generates ESPHome configuration for custom light presets based on JSON definitions.

### Usage

```bash
# Activate ESPHome environment first
workon esphome-stable

# Create example preset file
python scripts/generate_presets.py --create-example

# Generate preset configuration
python scripts/generate_presets.py [preset_file] [options]
```

### Options

- `--output-dir DIR`: Output directory (default: packages)
- `--style {buttons,select}`: Generation style (default: buttons)
- `--create-example`: Create example preset file and exit

### Examples

```bash
# Generate button-style presets
python scripts/generate_presets.py my-presets.json --style buttons

# Generate select-style presets
python scripts/generate_presets.py my-presets.json --style select
```

### Preset JSON Format

```json
{
  "presets": [
    {
      "name": "Office",
      "description": "Bright cool white for work",
      "temperature": 4500,
      "brightness": 1.0,
      "icon": "mdi:office-building"
    }
  ]
}
```

- `name`: Required - Preset display name
- `temperature`: Required - Color temperature in Kelvin (2200-6500)
- `brightness`: Required - Brightness level (0.1-1.0)  
- `description`: Optional - Human-readable description
- `icon`: Optional - Material Design icon name