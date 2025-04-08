# Monster Hunter Card Generator

This Python script generates image files of the cards from the React app and saves them to a folder, naming them according to the card names.

## Prerequisites

- Python 3.7 or higher
- Chrome browser installed
- React app running locally

## Installation

1. Install the required Python packages:

```
pip install -r requirements.txt
```

## Usage

1. Start the React development server:

```
npm run dev
```

2. Run the card generator script:

```
python card_generator.py
```

3. When prompted, enter the name of the output folder (or press Enter to use the default 'generated_cards' folder).

4. The script will:
   - Connect to the local React app
   - Take screenshots of each card (front and back)
   - Save them as PNG files in the specified folder
   - Name them according to the monster ID and behavior name

## Output

The generated files will follow this naming pattern:
```
{monster_id}_{behavior_name}_front.png
{monster_id}_{behavior_name}_back.png
```

For example:
```
chata_Tongue_Lash_front.png
chata_Tongue_Lash_back.png
```

## Troubleshooting

- Make sure the React app is running on http://localhost:5173 before starting the script
- If you encounter errors, check that Chrome is properly installed and accessible
- For WebDriver issues, you may need to update your Chrome browser or WebDriver version
