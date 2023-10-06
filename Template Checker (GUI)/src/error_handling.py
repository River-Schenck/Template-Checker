import tkinter as tk
from collections import defaultdict


class ValidationResult:
    def __init__(self):
        self.successes = []
        self.errors = defaultdict(list)
        self.warnings = defaultdict(list)
        self.par_styles = []
        self.actual_par_styles_fonts = []
        self.fonts = []
        self.fonts_postscript = []
        self.images = []
        self.links_folder_images = []

    def add_success(self, message, success_type="SUCCESS"):
        formatted_success = f"[{success_type}]: {message}"
        self.successes.append(formatted_success)

    def add_error(self, message, error_type="ERROR", page=None):
        formatted_error = f"[{error_type}]: {message}"
        key = page if page else "general"
        self.errors[key].append(formatted_error)

    def add_warning(self, message, warning_type="WARNING", page=None):
        formatted_warning = f"[{warning_type}]: {message}"
        key = page if page else "general"
        self.warnings[key].append(formatted_warning)

    def display_success_results(self, text_widget):
        text_widget.tag_configure(
            "success", foreground="green", font=("Open Sans", 16))
        for success in self.successes:
            text_widget.insert(tk.END, f"✅ [SUCCESS] {success}\n", "success")

    def display_error_results(self, text_widget):
        text_widget.tag_configure(
            "error", foreground="red", font=("Open Sans", 16))

        for key in sorted(self.errors.keys(), key=lambda x: (x != "general", int(x) if x != "general" else 0)):
            for error in self.errors[key]:
                text_widget.insert(tk.END, f"❌ {error}\n", "error")

    def display_warning_results(self, text_widget):
        text_widget.tag_configure(
            "warning", foreground="yellow", font=("Open Sans", 16))

        for key in sorted(self.warnings.keys(), key=lambda x: (x != "general", int(x) if x != "general" else 0)):
            for warning in self.warnings[key]:
                text_widget.insert(tk.END, f"⚠️ {warning}\n", "warning")

    def add_par_style(self, style):
        if style not in self.par_styles:
            self.par_styles.append(style)

    def display_par_styles(self, text_widget):
        text_widget.insert(tk.END, "\n--- Styles Used ---\n")
        for style in self.par_styles:
            text_widget.insert(tk.END, f"{style}\n")

    # If over ride, font from P Style may not actually be used
    def add_actual_par_style_fonts(self, par_style):
        if not any(item for item in self.actual_par_styles_fonts if item['par_style'] == par_style):
            self.actual_par_styles_fonts.append({
                'par_style': par_style
                # 'based_on' key is omitted until we know the relationship
            })

    def update_based_on(self, par_style, based_on_style):
        # Find the paragraph style in the list and update its based-on style
        for item in self.actual_par_styles_fonts:
            if item['par_style'] == par_style:
                item['based_on'] = based_on_style
                break

    def display_actual_par_styles_fonts(self, text_widget):
        text_widget.insert(tk.END, "\n--- Styles where Font is Used ---\n")
        for style_dict in self.actual_par_styles_fonts:
            par_style = style_dict.get('par_style')
            based_on_style = style_dict.get('based_on')

            if based_on_style:
                text_widget.insert(
                    tk.END, f"{par_style} Font Based on {based_on_style}\n")
            else:
                text_widget.insert(tk.END, f"{par_style}\n")

    def add_font(self, font):
        if font not in self.fonts:
            self.fonts.append(font)

    def display_fonts(self, text_widget):
        text_widget.insert(tk.END, "\n--- Fonts Used ---\n")
        for font in self.fonts:
            text_widget.insert(tk.END, f"{font}\n")

    def add_fonts_postscript(self, font_postscript):
        if font_postscript not in self.fonts_postscript:
            self.fonts_postscript.append(font_postscript)

    def display_fonts_postscript(self, text_widget):
        text_widget.insert(tk.END, "\n--- Fonts Postscript ---\n")
        for font in self.fonts_postscript:
            text_widget.insert(tk.END, f"{font}\n")

    def add_image(self, image):
        if image not in self.images:
            self.images.append(image)

    def add_links_folder_image(self, image):
        if image not in self.links_folder_images:
            self.links_folder_images.append(image)
