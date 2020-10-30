# Description

Converts Python project (input) to shareable PDF project (output) with sensitive informtion redacted.

Indended to censor entire function definitions only, while keeping function/class declarations, function/class documentation, and comments public.

Modify `settings.py` to indicate which project directories should be included in the conversion. Those with `is_public == True` will be entirely viewable. Populate `corner_cases` key with objects specifiying the declaration of a distinct function that should be censored in a script that is otherwise public.  

# Usage

1) modify `settings.py` to specify redaction rules for censoring sensitive information
2) run `python redact.py [relative_path_to_target_directory]`
3) share zipped copy of converted and redacted target project in the `projects` directory