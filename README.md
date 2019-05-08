# Precompiled Helper

This tool is intended to help you find out which headers are actually slowing down your compilation time and should be added to your precompiled headers.
By running a full preprocessor, this actually tells you how many times a given header was included in your cpp files.

It's intended to help you find that one header that every translation unit ends up including and put that in the precompiled header.

This is a very big WIP. Still remaining to do:

- [ ] Convert to pep8 style (I'm not a fan, but it's Python, so kinda have to...)
- [ ] Allow running from the command line without a configuration file.
- [ ] Clean up all the code.
- [ ] Package and so on.

## Dependencies

This requires the python [pcpp preprocessor](https://pypi.org/project/pcpp/).
```pip install pcpp```

## Example usage.

Check-out the included `0ad.json.example` configuration file, which is intended to parse some headers of the [0 A.D. video game.](https://play0ad.com).
Run the precompiled helper by running `python precompiled_helper.py --file [yourfile]`.
Results are outputed to `scores.csv` and two files recapping which headers get directly included where and what they directly include.

You can parse `scores.csv` with whatever you want, including Excel.
Personally I like to use r and the following script which shows you the 50 most included scripts.
```r
library(data.table)
data <- fread("scores.csv")
head(data[order(-n)], 50)
```