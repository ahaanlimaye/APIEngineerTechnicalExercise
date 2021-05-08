# APIEngineerTechnicalExercise
Python Script that converts Airplane Seatmap XML files that follow the format of either [seatmap1.xml](seatmap1.xml) or [seatmap2.xml](seatmap2.xml) into readable JSON files

## Usage
- Run `seatmap_parser.py` with a XML File as the argument (XML File must have the suffix "1" or "2" which correspond to the file formats of [seatmap1.xml](seatmap1.xml) and [seatmap2.xml](seatmap2.xml), respectively)
- After running, a new JSON file with the suffix "_parsed" will be created in the same directory
```
python seatmap_parser.py [XML_FILEPATH]
```

## Example
```
>>> python seatmap_parser.py seatmap1.xml
Successfully created JSON of seatmap1.xml in new file: seatmap1_parsed.json
```
