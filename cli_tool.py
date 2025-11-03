import os
import sys
from pathlib import Path
from typing import Optional
from datetime import datetime
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
from rich.markdown import Markdown
from rich.table import Table
from rich.align import Align
from rich.text import Text
from langchain_google_genai import ChatGoogleGenerativeAI
from docling.document_converter import DocumentConverter
from template import CompanyInfo, ContactInfo, CoverLetterContent, CoverLetterData, CoverLetterGenerator
from prompt import PROMPT
from dotenv import load_dotenv

load_dotenv()

# Initialize rich console
console = Console()

# File paths
DATA_DIR = Path.home() / ".cover_letter_generator"
CV_FILE = DATA_DIR / "saved_cv.txt"
CUSTOM_INSTRUCTION_FILE = DATA_DIR / "custom_instruction.txt"

DATA_DIR.mkdir(exist_ok=True)

class CoverLetterCLI:
    def __init__(self):
        self.api_key = os.getenv("GOOGLE_API_KEY", "")
        self.cv_text = ""
        self.job_listing = ""
        self.cover_letter = ""
        self.custom_instruction = ""
        self.load_saved_data()
        self.cover_letter_data: Optional[CoverLetterData] = None
        self.generator = CoverLetterGenerator()
        self.llm: ChatGoogleGenerativeAI = ChatGoogleGenerativeAI(model="gemini-flash-latest").with_structured_output(CoverLetterData)
        self.chain = PROMPT | self.llm

    def load_saved_data(self):
        """Load previously saved CV and job listing"""
        if CV_FILE.exists():
            self.cv_text = CV_FILE.read_text()
        if CUSTOM_INSTRUCTION_FILE.exists():
            self.custom_instruction = CUSTOM_INSTRUCTION_FILE.read_text()

    def save_cv(self, text: str):
        """Save CV to file"""
        CV_FILE.write_text(text)
        
    def extract_pdf(self, file_path: str) -> Optional[str]:
        """Extract text from PDF using Docling"""
        try:
            with console.status("[bold cyan]📄 Parsing PDF..."):
                converter = DocumentConverter()
                result = converter.convert(file_path)
                return result.document.export_to_markdown()
        except Exception as e:
            console.print(f"[red]❌ Error parsing PDF: {str(e)}")
            return None
    
    def get_cv_input(self):
        """Get CV input from user"""
        console.print("\n[bold cyan]📄 CV/Resume Input[/bold cyan]")
        console.print("[dim]Choose input method:[/dim]")
        console.print("1) Paste your CV\n2) Use a PDF\n3) Use saved CV\n")

        choice = input("Enter choice (1/2/3): ").strip()
        while choice not in ("1", "2", "3"):
            console.print("[red]Invalid choice. Please enter 1, 2 or 3.[/red]")
            choice = input("Enter choice (1/2/3): ").strip()

        choice_map = {
            "1": "paste",
            "2": "upload",
            "3": "use_saved"
        }
        method = choice_map[choice]

        if method == "paste":
            console.print("[dim]Paste your CV (press Ctrl+D when done, or type 'END' on a new line):[/dim]")
            lines = []
            while True:
                try:
                    line = input()
                    if line.strip().upper() == "END":
                        break
                    lines.append(line)
                except EOFError:
                    break
            self.cv_text = "\n".join(lines)

            if Confirm.ask("[cyan]Save this CV for future use?", console=console):
                self.save_cv(self.cv_text)
                console.print("[green]✅ CV saved!")

        elif method == "upload":
            pdf_path = Prompt.ask("[cyan]Enter PDF file path")
            if os.path.exists(pdf_path):
                extracted = self.extract_pdf(pdf_path)
                if extracted:
                    self.cv_text = extracted
                    console.print(f"[green]✅ Successfully extracted text from {pdf_path}")
                    if Confirm.ask("Save this CV for future use?", console=console):
                        self.save_cv(self.cv_text)
            else:
                console.print("[red]❌ File not found!")

        elif method == "use_saved" and self.cv_text:
            console.print("[green]✅ Using saved CV")
        else:
            console.print("[red]❌ No saved CV available!")
    
    def get_job_input(self):
        """Get job listing input from user"""
        console.print("\n[bold cyan]💼 Job Listing Input[/bold cyan]")
        console.print("[dim]Paste job listing (type 'END' on a new line, or press Ctrl+D):[/dim]")
        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            except EOFError:
                break
        self.job_listing = "\n".join(lines)
        if not self.job_listing.strip():
            console.print("[red]❌ No job listing provided![/red]")
    
    def get_custom_instruction(self):
        """Ask user for a custom instruction to guide the AI (fancy UI)"""
        console.print()
        header = Text("Custom Instruction for AI", style="bold magenta")
        desc = Text(
            "Describe tone, length, focus, keywords, or anything the AI should prioritize.\n"
            "Examples:\n"
            "  - Keep it concise and professional (≤ 200 words)\n"
            "  - Emphasize leadership and project management experience\n"
            "  - Use UK English and formal tone\n\n"
            "Type 'END' on a new line when finished, or press Ctrl+D.",
            style="dim"
        )
        console.print(Panel(Align.center(Text.assemble(header, "\n\n", desc)), border_style="magenta", subtitle="🛠️ Tailor the cover letter"))

        lines = []
        while True:
            try:
                line = input()
                if line.strip().upper() == "END":
                    break
                lines.append(line)
            except EOFError:
                break

        self.custom_instruction = "\n".join(lines).strip()
        if self.custom_instruction and len(self.custom_instruction) > 0:
            console.print("[green]✅ Custom instruction recorded![/green]")
            if Confirm.ask("Save this instruction for future use?", console=console):
                CUSTOM_INSTRUCTION_FILE.write_text(self.custom_instruction)
                console.print("[green]✅ Instruction saved!")
        else:
            console.print("[yellow]⚠️ No custom instruction provided — defaults will be used.[/yellow]")

    
    def generate_cover_letter(self):
        """Generate cover letter using AI"""
        if not self.api_key:
            console.print("[red]❌ GOOGLE_API_KEY not set. Please set it in your environment.")
            sys.exit(1)
        
        if not self.cv_text or not self.job_listing:
            console.print("[red]❌ Please provide both CV and job listing!")
            return False
        
        try:
            with Progress(
                SpinnerColumn(style="cyan"),
                TextColumn("[progress.description]{task.description}"),
                console=console
            ) as progress:
                progress.add_task("[cyan]🤖 AI is crafting your cover letter...", total=None)
                self.cover_letter_data = self.chain.invoke({
                            "cv_text": self.cv_text,
                            "job_listing": self.job_listing,
                            "user_instructions": self.custom_instruction
                        })
                return True
        except Exception as e:
            console.print(f"[red]❌ Error generating cover letter: {str(e)}")
            return False
    
    def display_cover_letter(self):
        """Render the generated CoverLetterData using rich Panels and Tables."""
        if not self.cover_letter_data:
            console.print("[red]❌ No cover letter generated yet!")
            return

        data = self.cover_letter_data

        # Contact / Applicant panel (compact table)
        contact_tbl = Table.grid(expand=True)
        contact_tbl.add_column(ratio=1)
        contact_tbl.add_column(ratio=2)
        contact_tbl.add_row(Text(data.contact.name or "-", style="bold magenta"), Text(data.contact.role or "-", style="cyan"))
        contact_tbl.add_row(Text("Email:", style="dim"), Text(data.contact.email or "-"))
        contact_tbl.add_row(Text("Phone:", style="dim"), Text(data.contact.phone or "-"))
        contact_tbl.add_row(Text("Address:", style="dim"), Text(data.contact.address or "-"))
        contact_tbl.add_row(Text("LinkedIn:", style="dim"), Text(data.contact.linkedin or "-"))
        contact_tbl.add_row(Text("GitHub:", style="dim"), Text(data.contact.github or "-"))
        contact_panel = Panel(contact_tbl, title="[bold magenta]👤 Applicant[/bold magenta]", border_style="magenta", padding=(1,2))

        # Company / Role panel
        company_tbl = Table.grid(expand=True)
        company_tbl.add_column(ratio=1)
        company_tbl.add_column(ratio=2)
        company_tbl.add_row(Text("Company:", style="dim"), Text(data.company.company or "-"))
        company_tbl.add_row(Text("Position:", style="dim"), Text(data.company.position or "-"))
        company_tbl.add_row(Text("Recipient:", style="dim"), Text(data.company.recipient or "-"))
        company_tbl.add_row(Text("Source:", style="dim"), Text(data.company.source or "-"))
        company_tbl.add_row(Text("Company news:", style="dim"), Text(data.company.company_news or "-"))
        company_panel = Panel(company_tbl, title="[bold green]🏢 Company[/bold green]", border_style="green", padding=(1,2))

        # Top row: contact + company
        top_row = Table.grid(expand=True)
        top_row.add_column(ratio=1)
        top_row.add_column(ratio=2)
        top_row.add_row(contact_panel, company_panel)

        # Content panel (cover letter body)
        content_txt = Text()
        content_txt.append((data.content.opening_salutation or "") + "\n\n", style="bold")
        content_txt.append((data.content.opening_paragraph or "") + "\n\n")
        content_txt.append((data.content.second_paragraph or "") + "\n\n")
        content_txt.append((data.content.closing_paragraph or "") + "\n\n")
        content_txt.append((data.content.signoff_paragraph or "") + "\n\n")
        content_txt.append((data.content.closing_salutation or "") + "\n", style="bold")

        content_panel = Panel(
            Align.left(content_txt),
            title="[bold cyan]📝 Generated Cover Letter[/bold cyan]",
            border_style="cyan",
            padding=(1,2)
        )

        console.rule("[bold]Cover Letter Preview[/bold]", style="cyan")
        console.print(top_row)
        console.print("\n")
        console.print(content_panel)
        console.rule(style="cyan")

    def export_cover_letter(self):
        """Export the generated cover letter to a text file"""
        if not self.cover_letter_data:
            console.print("[red]❌ No cover letter generated yet!")
            return
        filename = f"cover_letter_{self.cover_letter_data.company.company.replace(' ', '_')}"
        results = self.generator.create(
            self.cover_letter_data,
            filename=filename,
            export_pdf=True
        )
        
        console.print(f"[green]✅ Cover letter saved to {results.get('pdf')}")
    
    def show_saved_files(self):
        """Show saved CV and job listings"""
        console.print("\n[bold cyan]📁 Saved Files[/bold cyan]")
        
        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Type", style="cyan")
        table.add_column("Path", style="dim")
        table.add_column("Exists", style="green")

        table.add_row("CV", str(CV_FILE), "✓" if CV_FILE.exists() and len(CV_FILE.read_text()) > 0 else "✗")
        table.add_row("Custom Instruction", str(CUSTOM_INSTRUCTION_FILE), "✓" if CUSTOM_INSTRUCTION_FILE.exists() and len(CUSTOM_INSTRUCTION_FILE.read_text()) > 0 else "✗")

        console.print(table)
        
        if Confirm.ask("\n[yellow]Delete saved files?", console=console):
            if CV_FILE.exists():
                CV_FILE.unlink()
                console.print("[green]✅ CV deleted")
    
    def display_resume_markdown(self):
        """Display the CV/Resume in markdown format"""
        if not self.cv_text:
            console.print("[red]❌ No CV/Resume available!")
            return
        
        console.print("\n[bold cyan]📄 CV/Resume Preview[/bold cyan]")
        markdown = Markdown(self.cv_text)
        console.print(markdown)

    def show_welcome(self):
        """Display welcome message"""
        console.print(Panel.fit("[bold magenta]Welcome to the Cover Letter Generator CLI![/bold magenta]\n\n"
                                "Create personalized cover letters powered by AI.\n\n"
                                "Let's get started!", border_style="magenta"))
        
        if self.api_key:
            console.print("[green]✓ API Key configured[/green]")
        else:
            console.print("[yellow]⚠ Set GOOGLE_API_KEY environment variable[/yellow]")
        
        console.print(f"[dim]Data directory: {DATA_DIR}[/dim]\n")
    
    def show_menu(self):
        """Show main menu"""
        while True:
            console.print("\n[bold cyan]Main Menu[/bold cyan]")
            console.print("1) Input CV/Resume\n2) Input Job Listing\n3) Add Custom Instruction\n4) Generate Cover Letter\n5) View Generated Cover Letter\n6) Export Cover Letter as PDF\n7) View Saved Files\n8) View CV/Resume Preview\n9) Exit\n")
            
            choice = input("Enter choice (1-9): ").strip()
            if choice == "1":
                self.get_cv_input()
            elif choice == "2":
                self.get_job_input()
            elif choice == "3":
                self.get_custom_instruction()
            elif choice == "4":
                if self.generate_cover_letter():
                    console.print("[green]✅ Cover letter generated successfully!")
                else:
                    console.print("[red]❌ Failed to generate cover letter.")
            elif choice == "5":
                self.display_cover_letter()
            elif choice == "6":
                self.export_cover_letter()
            elif choice == "7":
                self.show_saved_files()
            elif choice == "8":
                self.display_resume_markdown()
            elif choice == "9":
                console.print("[bold magenta]👋 Goodbye![/bold magenta]")
                break
            else:
                console.print("[red]❌ Invalid choice. Please enter a number between 1 and 9.[/red]")
    
    def run(self):
        """Run the CLI tool"""
        self.show_welcome()
        self.show_menu()

def main():
    """Entry point"""
    try:
        cli = CoverLetterCLI()
        cli.run()
    except KeyboardInterrupt:
        console.print("\n[yellow]⚠ Interrupted by user")
        sys.exit(0)
    except Exception as e:
        console.print(f"[red]❌ Fatal error: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    main()