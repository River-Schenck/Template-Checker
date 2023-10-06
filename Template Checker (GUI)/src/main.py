from error_handling import ValidationResult
import tkinter as tk
from tkinter import filedialog
import tkinter.ttk as ttk
from enum import Enum, auto
import zipfile
import os
import shutil  # to delete the __MACOSX folder after unzipping
from lxml import etree as ET
from fontTools.ttLib import TTFont
import math


class States(Enum):
    GET_ZIP = auto()
    UNZIP_PACKAGE = auto()
    UNZIP_IDML = auto()
    PARSE_XML = auto()
    MASTERPAGE_CHECK = auto()
    PAR_CHECK = auto()
    HYPHENATION_CHECK = auto()
    OVERRIDES_CHECK = auto()
    FONTS_INCLUDED_CHECK = auto()
    OTF_TTF_FONT_CHECK = auto()
    VARIABLE_FONT_CHECK = auto()
    IMAGES_INCLUDED_CHECK = auto()
    LARGE_IMAGE_CHECK = auto()
    EMBEDDED_IMAGE_CHECK = auto()
    IMAGE_TRANSFORMATION_CHECK = auto()
    TABLE_CHECK = auto()
    AUTO_SIZE_TEXT_BOX_CHECK = auto()
    RESULTS = auto()
    IDLE = auto()
    EXIT = auto()


# **********************************************************
# Class: Image
# Description: A class to represent and manage image data.
# **********************************************************

class Image:
    def __init__(self, image_path):
        self.image_path = image_path
        self.image_name = os.path.basename(image_path)
        self.image_extension = os.path.splitext(self.image_name)[1]
        self.image_size_bytes = os.path.getsize(image_path)
        self.image_size_MB = self.convert_bytes_to_MB(self.image_size_bytes)

    def get_image_name(self):
        return self.image_name

    def get_image_extension(self):
        return self.image_extension

    def get_image_size(self):
        return self.image_size_MB

    def convert_bytes_to_MB(self, size_in_bytes):
        return round(size_in_bytes / (1024 ** 2), 2)

    def __str__(self):
        return f"Image Name: {self.image_name}\n" + \
               f"Image Extension: {self.image_extension}\n" + \
               f"Image Size: {self.image_size_MB} MB"


# **********************************************************
# Class: SourceFoldersParser
# Description: A class to parse and manage data from the source package.
# **********************************************************
class SourceFoldersParser:
    def __init__(self, document_links_folder_path, document_fonts_folder_path):
        self.document_links_folder_path = document_links_folder_path
        self.images_obj_list = self._extract_images_data()
        self.document_fonts_folder_path = document_fonts_folder_path
        self.document_fonts = self._extract_document_fonts()

    def _extract_images_data(self):
        images_obj_list = []
        for filename in os.listdir(self.document_links_folder_path):
            image_path = os.path.join(
                self.document_links_folder_path, filename)
            image_data = Image(image_path)
            images_obj_list.append(image_data)
        return images_obj_list

    def get_images_obj_list(self):
        return self.images_obj_list

    def print_images_obj_list(self):
        for image_data in self.images_obj_list:
            print(image_data)

    def _extract_document_fonts(self):
        document_fonts = []

        for filename in os.listdir(self.document_fonts_folder_path):
            if filename.endswith('.lst'):
                continue

            font_path = os.path.join(self.document_fonts_folder_path, filename)
            try:
                font = TTFont(font_path)
                # Name ID 1 is the font family name
                font_name = font["name"].getDebugName(1)
                font_type = "TrueType" if font.sfntVersion == "true" else "Other"
                variable_font = True if "fvar" in font else False
                document_fonts.append(FontFamily(
                    font_name, [font_name], variable_font, font_type))
            except Exception as e:
                print(f"Error processing font {filename}: {e}")

        return document_fonts

    def get_document_fonts(self):
        return self.document_fonts

    def print_document_fonts(self):
        print("\n".join(font.fontFamily for font in self.document_fonts))


# **********************************************************
# Class:TextFrame
# Description:
# **********************************************************
class TextFrame:
    def __init__(self, frame_id, parent_story_id, applied_object_style, auto_sizing_type=None, auto_sizing_reference_point=None, use_no_line_breaks=None):
        self.frame_id = frame_id
        self.parent_story_id = parent_story_id
        self.parent_story_obj = None
        self.applied_object_style = applied_object_style
        self.auto_sizing_type = auto_sizing_type
        self.auto_sizing_reference_point = auto_sizing_reference_point
        self.use_no_line_breaks = use_no_line_breaks
        self.is_auto_size = True if auto_sizing_type else False

    def from_xml_element(frame_element):
        id = frame_element.get("Self")
        parent_story_id = frame_element.get("ParentStory")
        applied_object_style = frame_element.get("AppliedObjectStyle")

        text_frame_pref = frame_element.find("TextFramePreference")
        auto_sizing_type = text_frame_pref.get(
            "AutoSizingType") if text_frame_pref is not None else None
        auto_sizing_reference_point = text_frame_pref.get(
            "AutoSizingReferencePoint") if text_frame_pref is not None else None
        use_no_line_breaks = text_frame_pref.get(
            "UseNoLineBreaksForAutoSizing") if text_frame_pref is not None else None

        return TextFrame(id, parent_story_id, applied_object_style, auto_sizing_type, auto_sizing_reference_point, use_no_line_breaks)

    def add_parent_story_obj(self, story):
        self.parent_story_obj = story

    def __str__(self):
        return f"TextFrame ID: {self.frame_id}\n" + \
               f"Parent Story: {self.parent_story_id}\n" + \
               f"Applied Object Style: {self.applied_object_style}\n" + \
               f"Is Auto Size: {self.is_auto_size}" + \
               f"Auto Sizing Type: {self.auto_sizing_type}\n" + \
               f"Auto Sizing Reference Point: {self.auto_sizing_reference_point}\n" + \
               f"Use No Line Breaks: {self.use_no_line_breaks}\n"


# **********************************************************
# Class: Link
# Description: A class to represent and manage image data.
# **********************************************************
class Link:
    def __init__(self, resource_uri, stored_state, item_transform, container_item_transform):
        self.resource_uri = resource_uri
        self.link_name = self.get_image_name()
        self.stored_state = stored_state
        self.item_transform = item_transform
        self.container_item_transform = container_item_transform

    def get_image_name(self):
        # Extract the image name from the URI
        return self.resource_uri.split("/")[-1]

    def get_stored_state(self):
        return self.stored_state

    def get_item_transform(self):
        return self.item_transform

    def get_container_item_transform(self):
        return self.container_item_transform

    def __str__(self):
        return f"Image Name: {self.link_name}\n" + \
               f"Resource URI: {self.resource_uri}\n" + \
               f"Stored State: {self.stored_state}\n" + \
               f"Item Transform: {self.item_transform}\n" + \
               f"container Item Transform: {self.container_item_transform}"


# **********************************************************
# Class: SpreadData
# Description:
# **********************************************************
class SpreadData:
    def __init__(self, page_name, extracted_links, root):
        self.page_name = page_name
        self.stories = []
        self.links_obj_list = extracted_links
        self.text_frame_obj_list = self._extract_text_frames(root)

    def _extract_text_frames(self, root):
        text_frames = []
        for frame_element in root.findall(".//TextFrame"):
            text_frame = TextFrame.from_xml_element(frame_element)
            text_frames.append(text_frame)
        return text_frames

    def get_page_name(self):
        return self.page_name

    def add_story(self, story_id):
        if story_id not in self.stories:
            self.stories.append(story_id)

    def get_links_obj_list(self):
        return self.links_obj_list

    def print_links_data(self):
        for link_data in self.links_obj_list:
            print(link_data)

    def __str__(self):
        link_names = [link.link_name for link in self.links_obj_list]
        return f"Page Name: {self.page_name}, Stories: {', '.join(self.stories)}, Links: {', '.join(link_names)}"


# **********************************************************
# Class: SpreadsParser
# Description:
# **********************************************************
class SpreadsParser:
    def __init__(self, spreads_xml_dir):
        self.spreads_xml_dir = spreads_xml_dir
        self.spreads_obj_list = self._extract_spreads_data()

    def _extract_spreads_data(self):
        spreads_obj_list = []

        # Iterate over each file in the directory
        for filename in os.listdir(self.spreads_xml_dir):
            if filename.endswith('.xml'):
                file_path = os.path.join(self.spreads_xml_dir, filename)
                tree = ET.parse(file_path)
                root = tree.getroot()
                extracted_links = self._extract_links_data(root)
                for spread in root.findall(".//Spread"):
                    for page in spread.findall("Page"):
                        page_name = page.get("Name")
                        spread_data = SpreadData(
                            page_name, extracted_links, root)

                        # Extract all stories associated with this page
                        for story_element in root.findall(f".//*[@ParentStory]"):
                            story_id = story_element.get("ParentStory")
                            if story_id:
                                spread_data.add_story(story_id)

                        spreads_obj_list.append(spread_data)

        return spreads_obj_list

    def _extract_links_data(self, root):
        links_obj_list = []

        for link_element in root.findall(".//Link"):
            resource_uri = link_element.get("LinkResourceURI")
            stored_state = link_element.get("StoredState")

            parent_element = link_element.getparent()
            item_transform = parent_element.get("ItemTransform")

            grandparent_element = parent_element.getparent()
            parent_item_transform = grandparent_element.get(
                "ItemTransform") if grandparent_element is not None else None

            image_data = Link(resource_uri, stored_state,
                              item_transform, parent_item_transform)
            links_obj_list.append(image_data)

        return links_obj_list

    def get_spreads_obj_list(self):
        return self.spreads_obj_list

    def get_page_by_story_id(self, story_id):
        for spread_data in self.spreads_obj_list:
            if story_id in spread_data.stories:
                return spread_data.page_name
        return None

    def print_spreads_obj_list(self):
        for spread_data in self.spreads_obj_list:
            print(spread_data)


# **********************************************************
# Class: Font
# Description:
# **********************************************************
class FontFamily:
    def __init__(self, fontFamily, fonts, variableFont, font_type):
        self.fontFamily = fontFamily
        self.fontType = font_type
        self.fonts = fonts
        self.variableFont = variableFont

    def get_font_family(self):
        return self.fontFamily

    def get_font_type(self):
        return self.fontType

    def is_variable_font(self):
        return self.variableFont

    def __str__(self):
        return f"Font Family: {self.fontFamily}, Font Type: {self.fontType}, Fonts: {', '.join(self.fonts)}, Variable Font: {self.variableFont}"


# **********************************************************
# Class: FontsParser
# Description:
# **********************************************************
class FontsParser:
    def __init__(self, fonts_xml_path):
        self.fonts_xml_path = fonts_xml_path
        self.font_families_from_xml = self._extract_fonts()
        self.used_font_families = []

    def _extract_fonts(self):
        if not os.path.exists(self.fonts_xml_path):
            raise FileNotFoundError(f"{self.fonts_xml_path} does not exist")

        tree = ET.parse(self.fonts_xml_path)
        root = tree.getroot()

        fonts_Families_list = []
        font_family_elements = root.findall(".//FontFamily")
        for font_family_element in font_family_elements:
            # For each FontFamily, find its nested Font tags
            fontFamily = font_family_element.get('Name')
            fonts = []
            variableFontFlag = False
            font_elements = font_family_element.findall(".//Font")
            for font_element in font_elements:
                name = font_element.get('Name')
                font_type = font_element.get('FontType')
                fonts.append(name)
                variableFont = font_element.get('NumDesignAxes')
                if variableFont is not None:
                    variableFontFlag = True
            fontFamilyObj = FontFamily(
                fontFamily, fonts, variableFontFlag, font_type)
            fonts_Families_list.append(fontFamilyObj)
        return fonts_Families_list

    def get_fonts_families_from_xml(self):
        return self.font_families_from_xml

    def print_font_families_from_xml(self):
        print("\n".join(str(font) for font in self.font_families_from_xml))

    def add_used_font_family(self, font_family_name):
        """Add a font family object to the list of used font families."""
        # Search for the font object in self.font_families_from_xml
        matching_font_obj = next(
            (font for font in self.font_families_from_xml if font.fontFamily == font_family_name), None)

        # If found and not already in the list, add to self.used_font_families
        if matching_font_obj and matching_font_obj not in self.used_font_families:
            self.used_font_families.append(matching_font_obj)

    def get_used_font_families(self):
        """Retrieve the list of used font families."""
        return self.used_font_families

    def print_used_font_families(self):
        """Print the list of used font families."""
        print("\n".join(self.used_font_families))


# **********************************************************
# Class: MasterPageParser
# Description:
# **********************************************************


class MasterPageParser:
    def __init__(self, masterspreads_dir):
        self.master_spreads_dir = masterspreads_dir
        self.unexpected_elements = []
        self.get_elements_from_all_files()

    def get_elements_from_file(self, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        master_spread = root.find('MasterSpread')
        elements = []
        if master_spread is not None:
            for child in master_spread:
                if child.tag not in ['Properties', 'Page']:
                    self.unexpected_elements.append(child.tag)
                elements.append(child.tag)
        return elements

    def get_elements_from_all_files(self):
        all_elements = {}
        for file_name in os.listdir(self.master_spreads_dir):
            if file_name.endswith('.xml'):
                file_path = os.path.join(self.master_spreads_dir, file_name)
                elements = self.get_elements_from_file(file_path)
                all_elements[file_name] = elements
        return all_elements

    def has_unexpected_elements(self):
        return bool(self.unexpected_elements)

    def print_unexpected_elements(self):
        if self.unexpected_elements:
            print("Unexpected Elements Found:")
            # Using set to remove duplicates
            for element in set(self.unexpected_elements):
                print(f"  - {element}")
        else:
            print("No unexpected elements found.")


# **********************************************************
# Class: PropertyBase
# Description:
# **********************************************************
class PropertyBase:
    def __init__(self, style_id, styles_parser):
        self.style_id = style_id
        self.styles_parser = styles_parser
        self.inherited_from = None
        self.property_name = self.get_property_name()
        self.value = self._resolve_inheritance(self.style_id)

    def get_property_name(self):
        raise NotImplementedError("Subclasses should implement this method")

    def _resolve_inheritance(self, style_id):
        inherited_value = self.styles_parser.get_all_properties(
            style_id).get(self.property_name)
        if not inherited_value:
            base_style = self.styles_parser.get_all_properties(
                style_id).get("BasedOn")
            if base_style:
                # Normalize the style_id
                if base_style.startswith("$ID/"):
                    base_style = "ParagraphStyle/" + base_style
                self.inherited_from = base_style
                return self._resolve_inheritance(base_style)
        return inherited_value

    def get_property_value(self):
        return self.value

    def get_inherited_from_value(self):
        return self.inherited_from

    def __str__(self):
        if self.inherited_from:
            return f"{self.property_name}: {self.value} (Inherited from: {self.inherited_from})"
        else:
            return f"{self.property_name}: {self.value} (Set directly)"


# -------------------------------------------
# Class: AppliedFont
# Inheritance: PropertyBase
# Description:
# -------------------------------------------
class AppliedFont(PropertyBase):
    def get_property_name(self):
        return "AppliedFont"


# -------------------------------------------
# Class: Hyphenation
# Inheritance: PropertyBase
# Description:
# -------------------------------------------
class Hyphenation(PropertyBase):
    def get_property_name(self):
        return "Hyphenation"


# **********************************************************
# Class: StylesParser
# Description: A parser class to extract paragraph styles from the provided XML path.
# **********************************************************
class StylesParser:
    def __init__(self, xml_path):
        self.tree = ET.parse(xml_path)
        self.root = self.tree.getroot()
        self.paragraph_styles = self._extract_paragraph_styles()

    def _extract_paragraph_styles(self):
        styles = {}
        for par_style in self.root.findall(".//ParagraphStyle"):
            style_id = par_style.get("Self")
            properties = par_style.find("Properties")
            style_properties = {}
            if properties is not None:
                for prop in properties:
                    style_properties[prop.tag] = prop.text
            style_properties["Hyphenation"] = par_style.get("Hyphenation")
            styles[style_id] = style_properties
        return styles

    def get_all_properties(self, style_id):
        return self.paragraph_styles.get(style_id, {})

    def print_par_style_names(self):
        for style_name in self.paragraph_styles.keys():
            print(style_name)


# **********************************************************
# Class: StoriesParser
# Description: A parser class to extract paragraph styles from the provided XML path.
# **********************************************************
class StoriesParser:
    def __init__(self, stories_dir, styles_parser, fonts_parser, spreads_parser):
        self.story_id = None
        self.stories_dir = stories_dir
        self.styles_parser = styles_parser
        self.fonts_parser = fonts_parser
        self.spreads_parser = spreads_parser
        self.used_font_families = []
        self.stories_data_list = []
        self.extract_stories_data()

    def extract_stories_data(self):
        for story_file in os.listdir(self.stories_dir):
            if story_file.endswith('.xml'):
                file_path = os.path.join(self.stories_dir, story_file)
                tree = ET.parse(file_path)
                root = tree.getroot()
                story_id = root.find("Story").get("Self")

                for story_element in root.findall("Story"):
                    story_id = story_element.get("Self")
                    story_data = StoryData(story_id, self.spreads_parser)

                    # Extract Paragraph Styles
                    for par_style_range in story_element.findall("ParagraphStyleRange"):
                        applied_par_style = par_style_range.get(
                            "AppliedParagraphStyle")

                        # Get properties of the paragraph style from Styles.xml
                        par_style_properties = self.styles_parser.get_all_properties(
                            applied_par_style)
                        applied_font = par_style_properties.get("AppliedFont")
                        based_on = par_style_properties.get("BasedOn")
                        hyphenation = par_style_properties.get("Hyphenation")

                        # Create a ParagraphStyle object
                        par_style = ParagraphStyle(
                            applied_par_style, self.styles_parser, self.fonts_parser, based_on, **par_style_properties)
                        story_data.add_paragraph_style(par_style)

                        # Extract Character Styles within the Paragraph Style
                        for char_style_range in par_style_range.findall("CharacterStyleRange"):
                            applied_char_style = char_style_range.get(
                                "AppliedCharacterStyle")
                            content_element = char_style_range.find("Content")
                            content = content_element.text if content_element is not None else None
                            applied_font_element = char_style_range.find(
                                "Properties/AppliedFont")
                            applied_font = applied_font_element.text if applied_font_element is not None else None
                            # Extracting overrides
                            overrides = {}
                            # Extracting attribute overrides
                            for attr, value in char_style_range.attrib.items():
                                if attr != "AppliedCharacterStyle":
                                    overrides[attr] = value
                                # Extracting child element overrides under Properties
                                properties_element = char_style_range.find(
                                    "Properties")
                                if properties_element is not None:
                                    for prop_child in properties_element:
                                        overrides[prop_child.tag] = prop_child.text
                            char_style = CharacterStyle(
                                applied_char_style, content, self.fonts_parser, applied_font, **overrides)
                            table_element = char_style_range.find("Table")
                            if table_element is not None:
                                char_style.add_table()
                            story_data.add_character_style(char_style)

                    self.stories_data_list.append(story_data)

    def get_story_by_id(self, story_id):
        """Returns the StoryData object for the given story_id."""
        for story_data in self.stories_data_list:
            if story_data.story_id == story_id:
                return story_data
        return None

    def get_stories_data(self):
        """Returns the list of extracted story data."""
        return self.stories_data_list

    def get_used_font_families(self):
        return self.used_font_families

    def print_used_font_families(self):
        if self.used_font_families:
            print("Used Font Families:")
            for font_family in self.used_font_families:
                print(f"  - {font_family}")
        else:
            print("No font families have been used.")

    def print_stories_data(self):
        """Prints the extracted story data for debugging purposes."""
        for story_data in self.stories_data_list:
            print(story_data)
            print("="*50)


# **********************************************************
# Class: StoryData
# Description: A class to hold and manage story data.
# **********************************************************
class StoryData:
    def __init__(self, story_id, spreads_parser):
        self.story_id = story_id
        self.page = spreads_parser.get_page_by_story_id(story_id)
        self.paragraph_styles = []
        self.character_styles = []

    def add_paragraph_style(self, par_style):
        if isinstance(par_style, ParagraphStyle):
            self.paragraph_styles.append(par_style)

    def add_character_style(self, char_style):
        if isinstance(char_style, CharacterStyle):
            self.character_styles.append(char_style)

    def get_paragraph_styles(self):
        return self.paragraph_styles

    def get_character_styles(self):
        return self.character_styles

    def get_story_text_content(self):
        return ''.join(char_style.get_content() for char_style in self.character_styles if char_style.get_content())

    def get_page(self):
        return self.page

    def get_all_fonts(self):
        return [char_style.applied_font for char_style in self.character_styles if char_style.applied_font]

    def __str__(self):
        return f"Story ID: {self.story_id}\n" + \
            f"Page: {self.page}\n" + \
            "\n".join(str(par_style) for par_style in self.paragraph_styles) + "\n" + \
            "\n".join(str(char_style) for char_style in self.character_styles)


# **********************************************************
# Class: ParagraphStyle
# Description: A class to represent and manage paragraph styles.
# **********************************************************
class ParagraphStyle:
    def __init__(self, style_id, styles_parser, fonts_parser, based_on=None, **other_properties):
        self.style_id = style_id
        self.styles_parser = styles_parser
        self.based_on = based_on
        self.applied_font_obj = AppliedFont(style_id, styles_parser)
        self.hyphenation_obj = Hyphenation(style_id, styles_parser)
        self.other_properties = other_properties
        self.add_used_paragraph_font(fonts_parser)

    def add_used_paragraph_font(self, fonts_parser):
        fonts_parser.add_used_font_family(
            self.applied_font_obj.get_property_value())

    def get_style_id(self):
        return self.style_id

    def has_hyphenation(self):
        return self.hyphenation_obj.get_property_value() == "true"

    def __str__(self):
        return f"Style ID: {self.style_id}\n" + \
            str(self.applied_font_obj) + "\n" + \
            str(self.hyphenation_obj) + "\n" + \
            "\n".join(f"{key}: {value}" for key, value in self.other_properties.items()
                      if key not in ["AppliedFont", "BasedOn", "Hyphenation"])


# ---------------------------------------------------
# Class: CharacterStyle
# Description: A class to represent and manage character styles.
# ---------------------------------------------------
class CharacterStyle:
    def __init__(self, applied_char_style, content, fonts_parser, applied_font=None, **overrides):
        self.applied_style = applied_char_style
        self.content = content
        self.applied_font = applied_font
        # Any attributes besides "AppliedCharacterStyle" and any properties
        self.overrides = overrides
        self.table_used = False
        self.add_used_character_font(fonts_parser)

    def add_used_character_font(self, fonts_parser):
        if self.applied_font is not None:
            fonts_parser.add_used_font_family(
                self.applied_font)

    def has_overrides(self):
        return bool(self.overrides)

    def get_overrides(self):
        return self.overrides

    def get_content(self):
        return self.content

    def add_table(self):
        self.table_used = True

    def has_table(self):
        return bool(self.table_used)

    def __str__(self):
        return f"Applied Character Style: {self.applied_style}\n" + \
               f"Content: {self.content}\n" + \
               f"Applied Font: {self.applied_font}\n" + \
               (f"Overrides: {self.overrides}\n" if self.has_overrides() else "")


# **********************************************************
# Class: FrontifyChecker
# Description:
# **********************************************************
class FrontifyChecker:
    def __init__(self):
        # Source ZIP
        self.source_file_path = None
        # Data
        self.current_dir = None
        self.data_folder = None
        self.unzipped_folder_name = None
        self.unzipped_folder_path = None
        document_fonts_folder_exists = True
        # Unarchived IDML
        self.idml_output_folder = None

        self.spreads_dir = None
        # XML Data
        self.styles_parser = None
        self.stories_parser = None
        self.stories_exist = True
        self.stories_object_list = None
        self.masterspreads_parser = None
        self.fonts_parser = None
        self.spreads_parser = None
        self.source_folders_parser = None
        # Initial State for State Machine, through GUI we already called States.GET_ZIP
        self.current_state = States.UNZIP_PACKAGE
        # State Machine States
        self.states = {
            States.GET_ZIP: self.get_zip_state,
            States.UNZIP_PACKAGE: self.unzip_package_state,
            States.UNZIP_IDML: self.unzip_idml_state,
            States.PARSE_XML: self.parse_xml,
            States.MASTERPAGE_CHECK: self.masterpage_check,
            States.PAR_CHECK: self.par_style_check,
            States.HYPHENATION_CHECK: self.hyphenation_check,
            States.OVERRIDES_CHECK: self.overrides_check,
            States.FONTS_INCLUDED_CHECK: self.fonts_included_check,
            States.OTF_TTF_FONT_CHECK: self.otf_ttf_font_check,
            States.VARIABLE_FONT_CHECK: self.variable_font_check,
            States.IMAGES_INCLUDED_CHECK: self.images_included_check,
            States.LARGE_IMAGE_CHECK: self.large_image_check,
            States.EMBEDDED_IMAGE_CHECK: self.embedded_image_check,
            States.IMAGE_TRANSFORMATION_CHECK: self.image_transformation_check,
            States.TABLE_CHECK: self.table_check,
            States.AUTO_SIZE_TEXT_BOX_CHECK: self.auto_size_text_box_check,
            States.RESULTS: self.results_state,
            States.IDLE: self.idle_state,
            States.EXIT: self.exit_state
        }
        # Validation Class
        self.results = ValidationResult()

    def run_state_machine(self):
        print(self.current_state)
        while self.current_state:
            self.current_state = self.states[self.current_state]()
            if (self.current_state == States.EXIT):
                return

        print(self.current_state)

    # ========================================================================================
    # State: GET_ZIP
    # PASS Next State Transition: NA
    # FAIL States Transition: NA
    # Description: GUI acts as an event handler and calls this function.
    # ========================================================================================
    def get_zip_state(self):
        source_file_path = filedialog.askopenfilename(
            filetypes=[("Zip files", "*.zip")])
        if source_file_path and source_file_path.endswith('.zip'):
            self.source_file_path = source_file_path
            print(f"Source File Path set to: {self.source_file_path}")
            return True
        else:
            self.results.add_error(
                f"File uploaded is not ZIP", "ZIP")
            return False

    # ========================================================================================
    # State: UNZIP_PACKAGE
    # PASS Next State Transition: UNZIP_IDML
    # FAIL States Transition: RESULTS
    # Description: Deletes 'data' folder, then create 'data' folder
    # ========================================================================================
    def unzip_package_state(self):
        self.current_dir = os.getcwd()
        self.data_folder = os.path.join(self.current_dir, 'data')

        if not self.cleanup_data_folder():
            return States.RESULTS

        if not self.extract_zip_to_data_folder():
            return States.RESULTS

        return States.UNZIP_IDML

    # ---------------------------------------------------
    # Function: cleanup_data_folder
    # Description: Deletes 'data' folder if it exists,
    # then creates a new 'data' folder.
    # ---------------------------------------------------
    def cleanup_data_folder(self):
        try:
            if os.path.exists(self.data_folder):
                shutil.rmtree(self.data_folder)
            os.makedirs(self.data_folder)
            return True
        except Exception as e:
            self.results.add_error(
                f"Error deleting the folder '{self.data_folder}': {str(e)}", "CODE ERROR")
            return False

    # ---------------------------------------------------
    # Function: extract_zip_to_data_folder
    # Description: Extracts ZIP into data folder. Then deletes the
    # __MACOSC folder from ZIP. Check only 1 folder in 'data' folder.
    # ---------------------------------------------------
    def extract_zip_to_data_folder(self):
        try:
            with zipfile.ZipFile(self.source_file_path, 'r') as zip_ref:
                zip_ref.extractall(self.data_folder)
                # to delete the __MACOSX folder after unzipping
                macosx_dir = os.path.join(self.data_folder, '__MACOSX')
                if os.path.exists(macosx_dir):
                    shutil.rmtree(macosx_dir)

            self.unzipped_folder_name = next(os.walk(self.data_folder))[
                1][0]  # Get the name of the unzipped folder
        except Exception as e:
            self.results.add_error(
                f"Failed to unzip the file. Error: {e}", "CODE ERROR")
            return False

        # Get all directories in the data_folder
        all_dirs = [d for d in os.listdir(
            self.data_folder) if os.path.isdir(os.path.join(self.data_folder, d))]

        # Check if there's only one main folder
        if len(all_dirs) != 1:
            self.results.add_error(
                "Multiple folders found in the provided package. Please ensure there's only one main folder after unzipping.", "FOLDER")
            return False
        self.unzipped_folder_path = os.path.join(
            self.data_folder, self.unzipped_folder_name)
        return True

    # ========================================================================================
    # State: UNZIP_IDML
    # PASS Next State Transition: PARSE_XML
    # FAIL States Transition: RESULTS
    # Description: Searches for the .idml files in the unzipped folder,
    # ensures there's only one .idml file, and then unarchives it.
    # ========================================================================================
    def unzip_idml_state(self):

        idml_path = self.validate_idml_files()
        if not idml_path:
            return States.RESULTS
        if not self.unarchive_idml_files(idml_path):
            return States.RESULTS
        return States.PARSE_XML

    # ---------------------------------------------------
    # Function: validate_idml_files
    # Description: Searches for .idml files in the unzipped folder path.
    # If no .idml files are found, an error is added to the results.
    # If multiple .idml files are found, an error is added to the results.
    # If one .idml file is found, its path is returned.
    # Returns: Path of the .idml file if one is found, False otherwise.
    # ---------------------------------------------------
    def validate_idml_files(self):
        idml_files = []
        for root, dirs, files in os.walk(self.unzipped_folder_path):
            for file in files:
                if file.endswith('.idml'):
                    idml_files.append(os.path.join(root, file))

        if len(idml_files) == 0:
            self.results.add_error(
                "No .idml file found in the provided package.", "IDML")
            return False
        elif len(idml_files) > 1:
            self.results.add_error(
                "Multiple .idml files found in the provided package. Please ensure there's only one .idml file.", "IDML")
            return False
        return idml_files[0]

    # ---------------------------------------------------
    # Function: unarchive_idml_files
    # Description: Unarchives the provided .idml file into a designated output folder.
    # If the unarchiving is successful, a success message is added to the results.
    # If there's an error during unarchiving, an error message is added to the results.
    # Args:
    #       idml_path: Path to the .idml file to be unarchived.
    # Returns: True if unarchiving is successful, False otherwise.
    # ---------------------------------------------------
    def unarchive_idml_files(self, idml_path):
        self.idml_output_folder = os.path.join(
            self.data_folder, 'Unarchived IDML')
        os.makedirs(self.idml_output_folder, exist_ok=True)
        try:
            with zipfile.ZipFile(idml_path, 'r') as zip_ref:
                zip_ref.extractall(self.idml_output_folder)
            self.results.add_success(
                f"No IDML issues found.", "IDML")
            return True
        except Exception as e:
            self.results.add_error(
                f"Failed to unzip the .idml file. Error: {e}", "CODE ERROR")
            return False

    # ========================================================================================
    # State: PARSE_XML
    # PASS Next State Transition:
    # FAIL States Transition: RESULTS
    # Description: Parses the XML to extract story data and paragraph styles.
    # ========================================================================================
    def parse_xml(self):
        # -----------------------------
        # Source Folders (Links, Document Fonts)
        # Init: SourceFoldersParser
        # -----------------------------
        # Check if 'Links' exists, if not create it to continue code flow
        document_links_folder_path = os.path.join(
            self.unzipped_folder_path, 'Links')
        if not os.path.exists(document_links_folder_path):
            os.makedirs(document_links_folder_path)
        # Check if 'Document Fonts' exists, if not create it to continue code flow
        document_fonts_folder_path = os.path.join(
            self.unzipped_folder_path, 'Document Fonts')
        if not os.path.exists(document_fonts_folder_path):
            self.document_fonts_folder_exists = False
            os.makedirs(document_fonts_folder_path)
        self.source_folders_parser = SourceFoldersParser(
            document_links_folder_path, document_fonts_folder_path)

        # -----------------------------
        # Spreads XML
        # Init: SpreadsParser
        # -----------------------------
        # Check if Spreads directory exists
        spreads_dir = os.path.join(
            self.idml_output_folder, 'Spreads')
        if not os.path.exists(spreads_dir):
            self.results.add_error(
                f"Spreads directory does not exist", "CODE ERROR")
            return States.RESULTS

        self.spreads_parser = SpreadsParser(
            spreads_dir)
        # -----------------------------
        # Fonts.XML
        # Init: FontsParser
        # -----------------------------
        # Check if Fonts.XML exists
        fonts_xml_path = os.path.join(
            self.idml_output_folder, 'Resources', 'Fonts.xml')
        if not os.path.exists(fonts_xml_path):
            self.results.add_error(
                f"Fonts.XML does not exist", "CODE ERROR")
            return States.RESULTS
        self.fonts_parser = FontsParser(
            fonts_xml_path)
        # -----------------------------
        # Styles.XML
        # Init: StylesParser
        # -----------------------------
        # Check if Styles.xml exists
        styles_xml_path = os.path.join(
            self.idml_output_folder, 'Resources', 'Styles.xml')
        if not os.path.exists(styles_xml_path):
            self.results.add_error(
                f"Styles.xml file does not exist", "CODE ERROR")
            return States.RESULTS
        # Initialize the StylesParser
        self.styles_parser = StylesParser(styles_xml_path)

        # -----------------------------
        # Stories XML
        # Init: StoriesParser
        # -----------------------------
        # Check if Stories directory exists
        stories_dir = os.path.join(self.idml_output_folder, 'Stories')
        if not os.path.exists(stories_dir):
            self.stories_exist = False
            self.results.add_warning(
                f"Stories directory does not exist", "PARAGRAPH_STYLE")
        else:
            # Initialize the StoriesParser and extract story data
            self.stories_parser = StoriesParser(
                stories_dir, self.styles_parser, self.fonts_parser, self.spreads_parser)
            self.stories_object_list = self.stories_parser.get_stories_data()

        # Map stories to text frames
        for spread in self.spreads_parser.spreads_obj_list:
            for text_frame in spread.text_frame_obj_list:
                text_frame.add_parent_story_obj(
                    self.stories_parser.get_story_by_id(text_frame.parent_story_id))

        # -----------------------------
        # MasterSpreads XML
        # Init: MasterPageParser
        # -----------------------------
        # Check if MasterSpreads directory exists
        masterspreads_dir = os.path.join(
            self.idml_output_folder, 'MasterSpreads')
        if not os.path.exists(masterspreads_dir):
            self.results.add_warning(
                f"MasterSpreads directory does not exist", "CODE ERROR")
        else:
            # Initialize the StoriesParser and extract story data
            self.masterspreads_parser = MasterPageParser(masterspreads_dir)

        return States.MASTERPAGE_CHECK

    # ========================================================================================
    # State: MASTERPAGE_CHECK
    # PASS Next State Transition: PAR_CHECK
    # FAIL States Transition: IMAGES_INCLUDED_CHECK
    # Description: Checks masterspreads_parser for unexprected elements (not properties or page)
    # ========================================================================================
    def masterpage_check(self):
        self.masterspreads_parser.print_unexpected_elements()  # Debug Print
        if self.masterspreads_parser.has_unexpected_elements():
            self.results.add_error(
                f"Master page was used.", "MASTERPAGE")
        else:
            self.results.add_success(
                "No master pages were used in the package.", 'MASTERPAGE')

        if self.stories_exist:
            return States.PAR_CHECK
        else:
            return States.IMAGES_INCLUDED_CHECK

    # ========================================================================================
    # State: PAR_STYLE_CHECK
    # PASS Next State Transition: HYPHENATION_CHECK
    # FAIL States Transition: NA
    # Description: Checks story paragraph styles (used styles) for default InDesign par styles.
    # ========================================================================================

    def par_style_check(self):
        self.stories_parser.print_stories_data()  # Debug Print
        par_style_flag = False
        for story in self.stories_object_list:
            for par_style in story.get_paragraph_styles():
                if par_style.get_style_id() in ["ParagraphStyle/$ID/NormalParagraphStyle", "ParagraphStyle/$ID/[No paragraph style]"]:
                    par_style_flag = True
                    self.results.add_error(
                        f"Text without paragraph style found on Page: {story.get_page()} in Text:'{story.get_story_text_content()}'", "PARAGRAPH_STYLE", story.get_page())
        if not par_style_flag:
            self.results.add_success(
                "Paragraph styles used on all text", "PARAGRAPH_STYLE")
        return States.HYPHENATION_CHECK

    # ========================================================================================
    # State: HYPHENATION_CHECK
    # PASS Next State Transition: OVERRIDES_CHECK
    # FAIL States Transition: NA
    # Description: Checks story paragraph styles for hyphenation enabled. The BaseProperty class
    #   parses for inheritance of hyphenation.
    # ========================================================================================

    def hyphenation_check(self):
        processed_styles = set()  # So we dont throw duplicate warnings
        hyphenation_flag = False
        for story in self.stories_object_list:
            for par_style in story.get_paragraph_styles():
                if par_style.has_hyphenation() and par_style.get_style_id() not in processed_styles:
                    hyphenation_flag = True
                    self.results.add_warning(
                        f"Hyphenation is enabled for style: {par_style.get_style_id()}", "HYPHENATION")
                    # Add the style_id to the set
                    processed_styles.add(par_style.get_style_id())
        if not hyphenation_flag:
            self.results.add_success(
                "Hyphenation disabled for all styles", "HYPHENATION")
        return States.OVERRIDES_CHECK

    # ========================================================================================
    # State: OVERRIDES_CHECK
    # PASS Next State Transition: FONTS_INCLUDED_CHECK
    # FAIL States Transition: NA
    # Description: Checks stories for character styles used. CharacterStyles class keeps track
    # of all additional properties or attributes used. We call a helper method to see if there
    # are any, if so, it is an override.
    # ========================================================================================
    def overrides_check(self):
        overrides_flag = False
        for story in self.stories_object_list:
            for char_style in story.get_character_styles():
                if char_style.has_overrides():
                    overrides_flag = True
                    self.results.add_warning(
                        f"Override found in text: '{char_style.get_content()}' on Page: {story.get_page()} ", "OVERRIDE", story.get_page())
        if not overrides_flag:
            self.results.add_success("No Overrides found", "OVERRIDE")
        return States.FONTS_INCLUDED_CHECK

    # ========================================================================================
    # State: FONTS_INCLUDED_CHECK
    # PASS Next State Transition: OTF_TTF_FONT_CHECK
    # FAIL States Transition: NA
    # Description: We get all used fonts (StoriesParser adds to FontsParser with override fonts)
    # and we get all fonts in document fonts. We compare them to see that all used fonts are
    # in the documents fonts folder.
    # ========================================================================================

    def fonts_included_check(self):
        used_font_families_objects = self.fonts_parser.get_used_font_families()
        # skip variable fonts
        used_font_families_names = [
            font_obj.get_font_family() for font_obj in used_font_families_objects if not font_obj.is_variable_font()]
        document_font_families = [font_obj.get_font_family(
        ) for font_obj in self.source_folders_parser.get_document_fonts()]
        fonts_included_flag = True
        for used_font in used_font_families_names:
            if used_font not in document_font_families:
                fonts_included_flag = False
                self.results.add_error(
                    f"Font family '{used_font}' is used but not found in the document fonts.", "FONT")
        if fonts_included_flag:
            self.results.add_success(
                "All fonts are included in package", "FONTS")
        return States.OTF_TTF_FONT_CHECK

    # ========================================================================================
    # State: OFT_TTF_FONT_CHECK
    # PASS Next State Transition: VARIABLE_FONT_CHECK
    # FAIL States Transition: NA
    # Description: From FontsParser we can get a list of all Font objects from Fonts.XML. We
    # verify that the font type is TrueType(.TTF) or OpenTypeCFF(.OTF)
    # ========================================================================================
    def otf_ttf_font_check(self):
        otf_ttf_font_flag = False
        for font_obj in self.fonts_parser.get_used_font_families():
            if font_obj.get_font_type() not in ['TrueType', 'OpenTypeCFF']:
                otf_ttf_font_flag = True
                self.results.add_error(
                    f"Font family '{font_obj.get_font_family()}' is not .OTF or .TTF format.", "FONT")
        if not otf_ttf_font_flag:
            self.results.add_success("All fonts .OTF or .TTF", "FONTS")
        return States.VARIABLE_FONT_CHECK

    # ========================================================================================
    # State: VARIABLE_FONT_CHECK
    # PASS Next State Transition: IMAGES_INCLUDED_CHECK
    # FAIL States Transition: NA
    # Description: From FontsParser we get a list of Font objects. We can call a helper function
    # to get the variable font attribute.
    # ========================================================================================
    def variable_font_check(self):
        variable_font_flag = False
        for font_obj in self.fonts_parser.get_used_font_families():
            if font_obj.is_variable_font():
                variable_font_flag = True
                self.results.add_error(
                    f"Font family '{font_obj.get_font_family()}' is a variable font.", "FONT")
        if not variable_font_flag:
            self.results.add_success("No variable fonts found", "FONTS")
        return States.IMAGES_INCLUDED_CHECK

    # ========================================================================================
    # State: IMAGES_INCLUDED_CHECK
    # PASS Next State Transition: LARGE_IMAGE_CHECK
    # FAIL States Transition: NA
    # Description: This state checks the consistency between the images used in the document (links) and the images present in the Links folder. It performs two main checks:
    # 1. Verifies that every image used in the document (as a link) is present in the Links folder.
    #    If an image is missing, it's flagged as an error.
    # 2. Identifies any images in the Links folder that are not used in the document. These are
    #    flagged as warnings since they might be unnecessary and could increase the document's size.
    # ========================================================================================
    def images_included_check(self):
        # Extract all the link names from the spreads.
        link_names = {link.get_image_name() for spread in self.spreads_parser.get_spreads_obj_list()
                      for link in spread.get_links_obj_list()}

        # Extract all the image names from the source folder.
        image_names = {image.get_image_name()
                       for image in self.source_folders_parser.get_images_obj_list()}
        images_used_flag = True
        # Check if all link names are found in the image names.
        missing_images = link_names - image_names
        if missing_images:
            for missing_image in missing_images:
                images_used_flag = False
                self.results.add_error(
                    f"Link '{missing_image}' is used but not found in the Links folder.", "IMAGE")

        # Check if there are any image names not used in links.
        unused_images = image_names - link_names
        if unused_images:
            for unused_image in unused_images:
                images_used_flag = False
                self.results.add_warning(
                    f"Image '{unused_image}' is present in the document but not used.", "IMAGE")

        if images_used_flag is True:
            self.results.add_success(
                f"All Links images used and found in Links folder", "IMAGE")
        return States.LARGE_IMAGE_CHECK

    # ========================================================================================
    # State: LARGE_IMAGE_CHECK
    # PASS Next State Transition: EMBEDDED_IMAGE_CHECK
    # FAIL States Transition: NA
    # Description: Checks each image in the source folder to determine if its size exceeds 20MB.
    # If an image is larger than 20MB, a warning is raised.
    # ========================================================================================
    def large_image_check(self):
        for image in self.source_folders_parser.get_images_obj_list():
            if image.get_image_size() > 20:
                self.results.add_warning(
                    f"Image '{image.get_image_name()}' {image.get_image_size()}MB is  large (over 20MB). Verify this large of image is needed for the use case.", "IMAGE")
        return States.EMBEDDED_IMAGE_CHECK

    # ========================================================================================
    # State: EMBEDDED_IMAGE_CHECK
    # PASS Next State Transition: IMAGE_TRANSFORMATION_CHECK
    # FAIL States Transition: NA
    # Description: Checks each link in the spreads to determine if its stored state is 'Embedded'.
    # If an image is embedded, an error is raised.
    # ========================================================================================
    def embedded_image_check(self):
        embedded_image_flag = False
        for spread in self.spreads_parser.get_spreads_obj_list():
            for link in spread.get_links_obj_list():
                if link.get_stored_state() == 'Embedded':
                    embedded_image_flag = True
                    self.results.add_error(
                        f"Image {link.get_image_name()} is embedded.", "IMAGE")

        if embedded_image_flag is False:
            self.results.add_success(
                f"No images are embedded", "IMAGE")
        return States.IMAGE_TRANSFORMATION_CHECK

    # ========================================================================================
    # State: IMAGE_TRANSFORMATION_CHECK
    # PASS Next State Transition: RESULTS
    # FAIL States Transition: NA
    # Description:
    # This method examines each image link within the document's spreads to identify any transformations applied. It checks for:
    # - Rotations: Determines if the image or its container has been rotated and by how many degrees.
    # - Skews: Identifies any skew transformations applied to the image or its container.
    # - Flips: Checks if the image or its container has been flipped horizontally or vertically.
    # For each detected transformation, an error message is generated specifying the type of
    # transformation, the image affected, and the page where the image is located.
    # ========================================================================================
    def image_transformation_check(self):
        transformation_detected_flag = False
        for spread in self.spreads_parser.get_spreads_obj_list():
            for link in spread.get_links_obj_list():
                item_transform = link.get_item_transform()
                container_transform = link.get_container_item_transform()
                file_name = link.get_image_name()
                page_name = spread.get_page_name()
                for idx, asset in enumerate([item_transform, container_transform]):
                    if asset:
                        a, b, c, d, x, y = map(float, asset.split())
                        context = "Image inside Container" if idx == 0 else "Image Container"
                        # Check for rotation
                        rotation_angle = math.atan2(b, a)
                        rotation_angle_degrees = math.degrees(rotation_angle)
                        if abs(rotation_angle_degrees) > 0.01:
                            transformation_detected_flag = True
                            self.results.add_error(
                                f"{context}: '{file_name}' on Page {page_name} has been rotated by {rotation_angle_degrees:.2f} degrees.", "IMAGES", page_name)
                        elif abs(b) > .01 or abs(c) > .01:
                            transformation_detected_flag = True
                            self.results.add_error(
                                f"{context}: '{file_name}' on Page: {page_name} has skew transformations. Skew factors: b={b}, c={c}", "IMAGES", page_name)
                        # Check for horizontal flip
                        if a < 0 and d > 0 and abs(rotation_angle_degrees) != 180:
                            transformation_detected_flag = True
                            self.results.add_error(
                                f"{context}: '{file_name}' on Page: {page_name} has a horizontal flip transformation.", "IMAGES", page_name)
                        # Check for vertical flip
                        if a > 0 and d < 0 and abs(rotation_angle_degrees) != 180:
                            transformation_detected_flag = True
                            self.results.add_error(
                                f"{context}: '{file_name}' on Page: {page_name} has a vertical flip transformation.", "IMAGES", page_name)

        if transformation_detected_flag is False:
            self.results.add_success(
                f"No images with transformations", "IMAGE")
        return States.TABLE_CHECK

    def table_check(self):
        for story in self.stories_object_list:
            for char_style in story.get_character_styles():
                if char_style.has_table():
                    page_name = story.get_page()
                    self.results.add_error(
                        f"Table was used on Page: {page_name}", "TABLE", page_name)
        return States.AUTO_SIZE_TEXT_BOX_CHECK

    def auto_size_text_box_check(self):
        # Verify not auto sizing from center
        for spread in self.spreads_parser.get_spreads_obj_list():
            for text_frame in spread.text_frame_obj_list:
                if text_frame.is_auto_size:
                    if text_frame.auto_sizing_reference_point is None:
                        story = text_frame.parent_story_obj
                        self.results.add_error(
                            f"Text Frame auto sizes from center Text: {story.get_story_text_content()}", "AUTOSIZE", story.page)
                str(text_frame)
        return States.RESULTS

    def results_state(self):
        gui.display_results()
        return States.EXIT

    def idle_state(self):
        print('idle')
        return States.EXIT

    def exit_state(self):
        print('exit')
        return States.EXIT


# **********************************************************
# Class: FrontifyGUI
# Description: A class designed to provide a graphical user interface (GUI) for the Frontify Template Checker.
# It allows users to select a ZIP file for validation, displays the validation results, and provides an option
# to reset the GUI for a new validation process.
# **********************************************************
class FrontifyGUI:
    def __init__(self, checker):
        self.checker = checker
        self.root = tk.Tk()
        self.root.title("Frontify Template Checker")
        self.root.geometry("1000x800")
        self.root.resizable(True, True)
        self.initialize_gui()

    def initialize_gui(self):
        logo = tk.PhotoImage(
            file="/Users/riverschenck/Documents/Code/Python/Template Checker (GUI)/media/frontify_logo_white_rgb.png")
        frontify_logo = logo.subsample(5, 5)
        logo_label = tk.Label(self.root, image=frontify_logo)
        logo_label.image = frontify_logo
        logo_label.pack(pady=20)

        self.folder_name_label = tk.Label(
            self.root, text="", font=("Arial", 14), anchor="w")
        self.folder_name_label.pack(pady=2, anchor="w", fill=tk.X, padx=20)

        self.results_display = tk.Text(
            self.root, wrap=tk.WORD, font=("Arial", 14))
        self.results_display.pack(pady=2, padx=20, expand=True, fill=tk.BOTH)

        self.select_button = ttk.Button(
            self.root,
            text="Select Zip File",
            command=self.select_zip_callback,
            padding=(20, 10)
        )
        self.select_button.pack(pady=20)

    def select_zip_callback(self):
        if self.select_button.cget("text") == "Select a new zip file":
            self.reset_gui()

        self.checker = FrontifyChecker()

        if self.checker.get_zip_state():
            self.folder_name_label.config(
                text=f"Template Name: {self.checker.source_file_path}")
            self.folder_name_label.update()

            # Update the state after a successful zip file selection
            self.checker.run_state_machine()
            self.select_button.config(text="Select a new zip file")
        else:
            # Handle the case where the user didn't select a valid zip file or canceled the dialog
            self.checker.results_state()

    def display_results(self):
        # Clear the Text widget
        self.results_display.delete(1.0, tk.END)

        # Display success, error, and warning results
        self.checker.results.display_success_results(self.results_display)
        self.checker.results.display_error_results(self.results_display)
        self.checker.results.display_warning_results(self.results_display)

    def reset_gui(self):
        """Resets the GUI to its initial state."""
        self.folder_name_label.config(text="")
        self.results_display.delete(1.0, tk.END)

    def run(self):
        self.root.mainloop()


if __name__ == "__main__":
    checker = FrontifyChecker()
    gui = FrontifyGUI(checker)
    gui.run()
