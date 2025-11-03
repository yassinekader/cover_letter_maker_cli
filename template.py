import subprocess
import json
from pathlib import Path
from typing import Optional
from pydantic import BaseModel, Field
from dataclasses import asdict


class ContactInfo(BaseModel):
    """Contact information for the applicant."""
    name: str
    email: str
    phone: str
    address: str
    linkedin: str = ""
    github: str = ""
    role: str = ""


class CompanyInfo(BaseModel):
    """Company and position information."""
    company: str
    position: str
    recipient: str
    source: str = ""
    company_news: str = ""


class CoverLetterContent(BaseModel):
    """Main content sections of the cover letter."""
    opening_salutation: str
    opening_paragraph: str
    second_paragraph: str
    closing_paragraph: str
    closing_salutation: str
    signoff_paragraph: str


class CoverLetterData(BaseModel):
    """Complete cover letter structured data."""
    contact: ContactInfo
    company: CompanyInfo
    content: CoverLetterContent

    def to_dict(self) -> dict:
        """Convert to dictionary for LaTeX template."""
        return {
            **self.contact.model_dump(),
            **self.company.model_dump(),
            **self.content.model_dump(),
        }

    def to_json(self, filepath: str = "cover_letter_data.json") -> Path:
        """Save structured data to JSON file."""
        path = Path(filepath)
        with open(path, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, indent=2, ensure_ascii=False)
        print(f"✓ Data saved to JSON: {path}")
        return path

    @classmethod
    def from_json(cls, filepath: str) -> "CoverLetterData":
        """Load structured data from JSON file."""
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)

        return cls(
            contact=ContactInfo(**data['contact']),
            company=CompanyInfo(**data['company']),
            content=CoverLetterContent(**data['content'])
        )


class CoverLetterGenerator:
    """Generate LaTeX cover letters and compile to PDF using local pdflatex."""

    LATEX_TEMPLATE = r"""
\documentclass[10pt,letter]{letter}
\usepackage[utf8]{inputenc}

%%================================
%% FROM TLCcoverletter.sty
%%================================
\usepackage[T1]{fontenc}
\usepackage[default,semibold]{sourcesanspro}
\usepackage[12pt]{moresize}
\usepackage{anyfontsize}
\usepackage{csquotes}
\usepackage[margin=.5in]{geometry}
\usepackage{xcolor}
\definecolor{highlight}{RGB}{61, 90, 128}
\usepackage{hyperref}
\hypersetup{colorlinks=true,urlcolor=highlight}
\newcommand{\bold}[1]{ {\bfseries #1}}
\pagenumbering{gobble}
\usepackage{standalone}
\usepackage{import}
\usepackage[english]{babel}
\usepackage{blindtext}
\usepackage{fancyhdr}

%%====================
%% CONTACT INFORMATION (used by header)
%%====================
\def\name{%(name)s}
\signature{\name}
\address{%(address)s \\ %(phone)s \\ \detokenize{%(email)s}}
\def\phone{%(phone)s}
\def\email{%(email)s}
\def\LinkedIn{%(linkedin)s}
\def\github{%(github)s}
\def\role{%(role)s}

%%====================
%% Company Info
%%====================
\def\hm{}
\def\position{%(position)s}
\def\company{%(company)s}
\def\source{%(source)s}
\def\companynews{%(company_news)s}

%%==================
%% Header file (_header)
%%==================
\fancypagestyle{plain}{%%
\fancyhf{}
\lhead{\phone \\
    \href{mailto:\email}{\email}}
\chead{%%
    \centering {\Large \bold\name} \\
    {\color{highlight} \large{\role}}}
\rhead{
    %%Portfolio: \href{https://yassinekader.dev}{yassinekader.dev}\\
    \href{https://github.com/\github}{github.com/\github} \\
    \href{https://www.linkedin.com/in/\LinkedIn}{linkedin.com/in/\LinkedIn}}
\renewcommand{\headrulewidth}{2pt}%%
\renewcommand{\headrule}{\hbox to\headwidth{%%
  \color{highlight}\leaders\hrule height \headrulewidth\hfill}}
}
\pagestyle{plain}

\setlength{\headheight}{90pt}
\setlength{\headsep}{0pt}

\makeatletter
\let\ps@empty\ps@plain
\let\ps@firstpage\ps@plain
\makeatother

%%==================
%% Document begins
%%==================
\begin{document}
\begin{letter}{%(recipient)s}

\opening{%(opening_salutation)s}

\setlength\parindent{.5in}

%(opening_paragraph)s

%(second_paragraph)s

%(closing_paragraph)s

%(signoff_paragraph)s

\closing{%(closing_salutation)s}

\end{letter}
\end{document}
"""

    def __init__(self):
        """Initialize the cover letter generator."""
        self.output_dir = Path("cover_letters")
        self.output_dir.mkdir(exist_ok=True)

    def _escape_latex_safe(self, text: str) -> str:
        """Escape special LaTeX characters (but NOT '%')."""
        replacements = {
            '&': r'\&',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'\textasciitilde{}',
            '^': r'\textasciicircum{}',
        }

        for char, replacement in replacements.items():
            text = text.replace(char, replacement)
        return text

    def generate_latex(self, cover_letter: CoverLetterData) -> str:
        """
        Generate LaTeX content from structured data.

        Args:
            cover_letter: CoverLetterData object

        Returns:
            Formatted LaTeX string
        """
        data = cover_letter.to_dict()

        safe_keys = set(cover_letter.content.model_dump().keys())
        safe_keys.add('github')
        safe_keys.add('linkedin')
        safe_keys.add('email')

        processed_data = {}
        for key, value in data.items():
            if not isinstance(value, str):
                processed_data[key] = value
                continue
            
            temp_value = value

            if key not in safe_keys:
                temp_value = self._escape_latex_safe(temp_value)

            processed_data[key] = temp_value.replace('%', '%%')

        return self.LATEX_TEMPLATE % processed_data

    def save_latex(self, latex_content: str, filename: str) -> Path:
        """Save LaTeX content to a file."""
        filepath = self.output_dir / f"{filename}.tex"
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(latex_content)
        print(f"✓ LaTeX file saved: {filepath.resolve()}")
        return filepath

    def compile_to_pdf_pdflatex(self, latex_file: Path) -> Optional[Path]:
        """
        Compile LaTeX to PDF using local pdflatex.

        Args:
            latex_file: Path to the .tex file

        Returns:
            Path to the generated PDF, or None if failed
        """
        try:
            print(f"Compiling {latex_file.name} to PDF using pdflatex...")

            result = subprocess.run(
                [
                    'pdflatex',
                    '-interaction=nonstopmode',
                    '-output-directory', str(self.output_dir),
                    str(latex_file)
                ],
                capture_output=True,
                text=True,
                timeout=30,
                encoding='utf-8',
                errors='ignore'
            )

            pdf_path = self.output_dir / f"{latex_file.stem}.pdf"

            if result.returncode == 0 and pdf_path.exists():
                print(f"✓ PDF generated successfully: {pdf_path}")
                subprocess.run(
                    ['pdflatex', '-interaction=nonstopmode', '-output-directory', str(self.output_dir), str(latex_file)],
                    capture_output=True, text=True, timeout=30, encoding='utf-8', errors='ignore'
                )
                return pdf_path
            else:
                print("✗ PDF generation failed")
                print("--- pdflatex Error Output ---")
                print(result.stdout)
                print("-----------------------------")
                return None

        except FileNotFoundError:
            print("✗ pdflatex not found. Please install a LaTeX distribution:")
            print("  Windows: https://miktex.org/download")
            print("  macOS: brew install --cask mactex")
            print("  Linux: sudo apt-get install texlive-latex-base texlive-latex-extra")
            return None
        except subprocess.TimeoutExpired:
            print("✗ pdflatex compilation timed out")
            return None
        except Exception as e:
            print(f"✗ An unexpected error occurred: {e}")
            return None

    def create(self, cover_letter: CoverLetterData, filename: str,
               export_pdf: bool = True) -> dict:
        """
        Create a cover letter from structured data.

        Args:
            cover_letter: CoverLetterData object
            filename: Base filename for output files
            export_pdf: Whether to generate PDF

        Returns:
            Dictionary with paths to generated files
        """
        results = {}

        latex_content = self.generate_latex(cover_letter)
        latex_path = self.save_latex(latex_content, filename)
        results['latex'] = str(latex_path)

        if export_pdf:
            pdf_path = self.compile_to_pdf_pdflatex(latex_path)
            if pdf_path:
                results['pdf'] = str(pdf_path.resolve())

        return results