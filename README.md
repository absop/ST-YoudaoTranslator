# Translators
A beautiful translation plugin for Sublime Text.
![Youdao - Default](image/default.png)


## Installation
The following steps assume that you already have [Package Control](https://packagecontrol.io/) installed.

1. Copy the URL of this repository: <https://github.com/absop/Translators>
2. Enter into Sublime Text, press down the shortcut <kbd>Ctrl+Shift+P</kbd> to enter into **Command Palette**
3. Input the command `pcar(Package Control: Add Repository)`
4. Press down the shortcut <kbd>Ctrl+V</kbd>, then <kbd>Enter</kbd>
5. Using **Package Control** to install this package
   1. Press down <kbd>Ctrl+Shift+P</kbd>
   2. Input `pcip(Package Control: Install Package)`
   3. Input `Translators`


## Key Binding
|              Keys               | Features                                                |
| :-----------------------------: | ------------------------------------------------------- |
| <kbd>alt+y, alt+t</kbd> | Translate words with `Youdao translator`               |
| <kbd>alt+y, alt+c</kbd> | Copy translation result                                 |
| <kbd>alt+y, alt+i</kbd> | Insert the translation result next to the original text |
| <kbd>alt+y, alt+r</kbd> | Replace the original text with translation result       |


## Advanced Features
To improve translation results, you can go [HERE](https://ai.youdao.com/) to register and obtain a app-key for **youdao translator**, then fill them in the settings file.

You can find a lot about this on the Internet.

The following image shows a sample of translation with `app-key`, notice the difference between it and the above translation(without 'app-key').
![Youdao - Enhanced](image/enhanced.png)


## TODO
- [ ] Add checkbox for every `translation` and `explanation`, select to copy/insert/replace.
- [ ] Improve the showing of results.
- [ ] Consider to cache translation results.
