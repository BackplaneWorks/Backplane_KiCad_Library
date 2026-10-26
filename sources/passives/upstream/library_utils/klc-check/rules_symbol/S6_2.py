import re
from collections import Counter

from rulebase import isValidName
from rules_symbol.rule import KLCRule

DISALLOWED_FILLER_TOKENS = frozenset(
    [
        "and",
        "or",
        "the",
        "a",
        "an",
        "of",
        "in",
        "on",
        "at",
        "to",
        "with",
        "by",
        "for",
        "from",
        "as",
        "into",
        "onto",
        "upon",
        "over",
        "under",
        "through",
        "between",
        "among",
        "within",
        "without",
        "about",
        "after",
        "before",
        "during",
        "since",
        "until",
        "while",
        "till",
        "throughout",
        "along",
        "across",
        "against",
        "behind",
        "beside",
        "beyond",
        "inside",
        "outside",
    ]
)

ALLOWED_FIELDS = frozenset(
    [
        "Reference",
        "Value",
        "Datasheet",
        "Description",
        "Footprint",
        "Sim.Device",
        "Sim.Enable",
        "Sim.Library",
        "Sim.Name",
        "Sim.Params",
        "Sim.Pins",
        "Sim.Type",
        "ki_keywords",
        "ki_fp_filters",
        "ki_locked",
        "ki_description",
    ]
)


class Rule(KLCRule):
    """Symbol fields and metadata filled out as required"""

    def checkReference(self) -> bool:
        fail = False
        ref = self.component.get_property("Reference")
        if not ref:
            self.error("Component is missing Reference field")
            # can not do other checks, return
            return True

        if (not self.component.is_graphic_symbol()) and (
            not self.component.is_power_symbol()
        ):
            if ref.is_hidden:
                self.error("Reference field must be VISIBLE")
                fail = True
        else:
            if not ref.is_hidden:
                self.error(
                    "Reference field must be INVISIBLE in graphic symbols or"
                    " power-symbols"
                )
                fail = True

        return fail

    def checkValue(self) -> bool:
        fail = False

        prop = self.component.get_property("Value")
        if not prop:
            self.error("Component is missing Value field")
            # can not do other checks, return
            return True
        name = prop.value

        if name.startswith('"') and name.endswith('"'):
            name = name[1:-1]

        if (not self.component.is_graphic_symbol()) and (
            not self.component.is_power_symbol()
        ):
            if not name == self.component.name:
                self.error(
                    "Value {val} does not match component name.".format(val=name)
                )
                fail = True
            # name field must be visible!
            if prop.is_hidden:
                self.error("Value field must be VISIBLE")
                fail = True
        else:
            if (not ("~" + name) == self.component.name) and (
                not name == self.component.name
            ):
                self.error(
                    "Value {val} does not match component name.".format(val=name)
                )
                fail = True

        if not isValidName(
            self.component.name,
            self.component.is_graphic_symbol(),
            self.component.is_power_symbol(),
        ):
            self.error(
                "Symbol name '{val}' contains invalid characters as per KLC 1.7".format(
                    val=self.component.name
                )
            )
            fail = True

        return fail

    def checkFootprint(self) -> bool:
        # Footprint field must be invisible
        fail = False

        prop = self.component.get_property("Footprint")
        if not prop:
            self.error("Component is missing Footprint field")
            # can not do other checks, return
            return True

        if not prop.is_hidden:
            self.error("Footprint field must be INVISIBLE")
            fail = True

        return fail

    def checkDatasheet(self) -> bool:
        # Datasheet field must be invisible
        fail = False

        ds = self.component.get_property("Datasheet")
        if not ds:
            self.error("Component is missing Datasheet field")
            # can not do other checks, return
            return True

        if not ds.is_hidden:
            self.error("Datasheet field must be INVISIBLE")
            fail = True

        # more checks for non power or non graphics symbol
        if (not self.component.is_graphic_symbol()) and (
            not self.component.is_power_symbol()
        ):
            # Datasheet field must not be empty
            if ds.value == "":
                self.error("Datasheet field must not be EMPTY")
                fail = True
            if ds.value and len(ds.value) > 2:
                link = False
                links = ["http", "www", "ftp"]
                if any([ds.value.startswith(i) for i in links]):
                    link = True
                elif ds.value.endswith(".pdf") or ".htm" in ds.value:
                    link = True

                if not link:
                    self.warning(
                        "Datasheet entry '{ds}' does not look like a URL".format(
                            ds=ds.value
                        )
                    )
                    fail = True

        return fail

    def checkExtraFields(self) -> bool:
        fail = False

        # iterate over all fields
        for field in self.component.properties:
            if field.name not in ALLOWED_FIELDS and not field.is_private():
                self.warning(f"Found a unexpected property with the name {field.name}")
                fail = True

        return fail

    def checkPrivateFields(self) -> bool:
        fail = False

        # iterate over all fields
        for field in self.component.properties:
            # in this check we only care about private fields
            if not field.is_private():
                continue

            # so far we only have one check for private fields
            # which is that they are not allowed unless they start with the "KLC_" prefix
            if not field.name.startswith("KLC_"):
                self.warning(
                    "Private fields are not allowed unless they start with the KLC_ prefix."
                )
                self.warningExtra(f'Found "{field.name}" with value "{field.value}"')
                fail = True
        return fail

    def checkDescription(self) -> bool:
        dsc = self.component.get_property("Description")
        if not dsc:
            # can not do other checks, return
            if self.component.is_power_symbol():
                return True
            else:
                self.error("Missing Description field on 'Properties' tab")
                return True

        # Symbol name should not appear in the description
        desc = dsc.value
        if self.component.name.lower() in desc.lower():
            self.warning("Symbol name should not be included in description")

        return False

    def _checkKeywordsSpecialCharacters(self, keywords: str) -> bool:
        """
        Check keywords for special characters such as "," or "." etc
        """
        # find special chars.
        # A dot followed by a non-word char is also considered a violation.
        # This allows 3.3V but prevents 'foobar. buzz'
        forbidden_matches = re.findall(r"\.\W|\.$|[,:;?!<>]", keywords)
        if forbidden_matches:
            self.error(
                "Symbol keywords contain forbidden characters: {}".format(
                    forbidden_matches
                )
            )
        return len(forbidden_matches) > 0

    def _tokenize_keywords(self, keywords: str, split_sub_tokens=True) -> list[str]:
        """
        Tokenize the keywords string into a list of tokens,
        splitting on whitespace and removing leading/trailing whitespace.

        NOTE: This doesn't only split into tokens on whitespace, but also
        into sub-tokens separated by dash.

        Example:
        "foo bar-baz" -> ["foo", "bar", "baz"]

        The tokens are returned as lowercase strings.
        """
        split_regex = r"\s+|-" if split_sub_tokens else r"\s+"
        return [token.strip().lower() for token in re.split(split_regex, keywords)]

    def _tokenize_description(
        self, description: str, split_sub_tokens=True
    ) -> list[str]:
        """
        Similar to _tokenize_keywords but takes into account that
        the description *may* contain special characters, which would cause
        tokens such as "opamp," to appear in the list.

        Also, the description may contain words more than once.
        """
        # Remove everything non-alphanumeric except for dash and whitespace
        description = re.sub(r"[^\w\s-]", "", description)
        split_regex = r"\s+|-" if split_sub_tokens else r"\s+"
        tokens = [token.strip().lower() for token in re.split(split_regex, description)]

        # Remove duplicates from tokens and return, preserving the order
        tokens = list(set(tokens))
        return tokens

    def _checkKeywordsDuplicateTokens(self, keywords: str, descriptions: str) -> bool:
        """
        Check for duplicate tokens in the keywords
        """
        # First check for pure duplicates e.g. "single opamp single"
        tokens = self._tokenize_keywords(keywords, split_sub_tokens=False)

        # Check if any token appears more than once
        token_counts = Counter(tokens)
        duplicate_tokens = {token for token, count in token_counts.items() if count > 1}
        if duplicate_tokens:
            self.warning(
                f"S6.2.7: Symbol keywords contain duplicate keywords: {duplicate_tokens}"
            )

        # Now check if any token appears as a sub-token,
        # e.g. "single opamp highspeed-opamp"
        # NOTE: We ignore tokens here which already appeared as full
        # tokens in the previous step (for usability)
        tokens_and_subtokens = self._tokenize_keywords(keywords, split_sub_tokens=True)
        token_counts = Counter(tokens_and_subtokens)
        duplicate_sub_tokens = {
            token for token, count in token_counts.items() if count > 1
        }
        duplicate_sub_tokens -= duplicate_tokens  # see NOTE above
        if duplicate_sub_tokens:
            self.warning(
                "S6.2.7: Symbol keywords contain duplicate sub-tokens"
                + f" (= dash-separated tokens): {duplicate_sub_tokens}"
            )

        # Now check if any tokens from the description appear in the keywords
        # NOTE: We remove tokens here which are already duplicate in the keywords
        description_tokens = self._tokenize_description(descriptions)
        all_tokens = tokens_and_subtokens + description_tokens
        duplicate_desc_keyword_tokens = {
            token for token, count in Counter(all_tokens).items() if count > 1
        }
        duplicate_desc_keyword_tokens -= duplicate_tokens  # see NOTE above
        duplicate_desc_keyword_tokens -= duplicate_sub_tokens  # see NOTE above
        if duplicate_desc_keyword_tokens:
            self.warning(
                "S6.2.7: Symbol keywords contain tokens which already appear "
                + f"in description: {duplicate_desc_keyword_tokens}"
            )

        return len(duplicate_tokens) > 0

    def _checkKeywordFillerWords(self, tokenized_keywords: list[str]) -> bool:
        """
        S6.2.7b
        Check for filler words such as "and"
        """
        # Check if any of the tokens are in the disallowed set
        forbidden_matches = set(tokenized_keywords) & DISALLOWED_FILLER_TOKENS
        if forbidden_matches:
            self.error(
                f"S6.2.7b: Symbol keywords contain forbidden filler words: {forbidden_matches}"
            )
        return len(forbidden_matches) > 0

    def _checkCommonKeywordAliases(self, keywords, description):
        # Split
        keywords_tokens = self._tokenize_keywords(keywords, split_sub_tokens=False)
        keywords_subtokens = self._tokenize_keywords(keywords, split_sub_tokens=True)

        description_tokens = self._tokenize_description(
            description, split_sub_tokens=False
        )
        description_subtokens = self._tokenize_description(
            description, split_sub_tokens=True
        )

        all_tokens = keywords_tokens + description_tokens
        all_subtokens = keywords_subtokens + description_subtokens

        _return = False
        # Opamp <=> operational amplifier
        if "operational" in all_subtokens and "amplifier" in description_tokens:
            if "opamp" not in all_subtokens:
                self.warning(
                    "Metadata contains 'operational amplifier', please add 'opamp' to the keywords"
                )
                _return = True
        if "opamp" in all_subtokens and not (
            "operational" in all_subtokens and "amplifier" in all_subtokens
        ):
            self.warning(
                "Metadata contains 'opamp', please add 'operational-amplifier' to the keywords"
            )
            _return = True

        # LDO <=> low-dropout ... regulator
        if "low-dropout" in all_tokens and "regulator" in all_subtokens:
            if "ldo" not in all_tokens:
                self.warning(
                    "Metadata contains 'low-dropout .. regulator', please add 'ldo' to the keywords"
                )
                _return = True
        if "ldo" in all_tokens and not (
            "low-dropout" in all_tokens and "regulator" in all_subtokens
        ):
            self.warning(
                "Metadata contains 'LDO', please add 'low-dropout' and 'regulator' to the keywords"
            )
            _return = True

        return _return

    def checkKeywords(self) -> bool:
        keywords_property = self.component.get_property("ki_keywords")
        if not keywords_property:
            # can not do other checks, return
            if self.component.is_power_symbol():
                return True
            else:
                self.warning(
                    "Missing or empty Keywords field on 'Properties' tab. "
                    + "If you have nothing to add here, add the manufacturer e.g. 'texas'"
                )
                return True
        else:  # have non-empty keywords
            keywords = keywords_property.value
            # Tests on raw keywords
            _result = self._checkKeywordsSpecialCharacters(keywords)

            # Tests on tokenized keywords
            keyword_tokens = self._tokenize_keywords(keywords)
            _result |= self._checkKeywordFillerWords(keyword_tokens)

            # Tests on description and tokenized keywords
            description_property = self.component.get_property("Description")
            description = description_property.value if description_property else ""

            # Skip duplicate token checks

            # Other checks
            _result |= self._checkCommonKeywordAliases(keywords, description)

            return _result

    def check(self) -> bool:
        # Check for extra fields. How? TODO

        # extraFields = False

        return any(
            [
                self.checkReference(),
                self.checkValue(),
                self.checkFootprint(),
                self.checkDatasheet(),
                self.checkDescription(),
                self.checkKeywords(),
                self.checkPrivateFields(),
                self.checkExtraFields(),
            ]
        )

    def fix(self) -> None:
        """
        Proceeds the fixing of the rule, if possible.
        """
        self.info("not supported")
        self.recheck()
