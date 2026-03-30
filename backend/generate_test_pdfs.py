import os
from fpdf import FPDF

# Ensure the output directory exists
pdf_dir = os.path.join(os.path.dirname(__file__), "test_pdfs")
os.makedirs(pdf_dir, exist_ok=True)

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(w=0, h=10, text="Official Fictional Documents Archive", border=False, align="C", new_x="LMARGIN", new_y="NEXT")
        self.ln(10)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(w=0, h=10, text=f"Page {self.page_no()}", align="C")

documents = [
    {
        "filename": "Galactic_Calendar_Rev42.pdf",
        "title": "Galactic Standard Calendar Revision 42",
        "content": (
            "The Galactic Standard Calendar (GSC) has been updated to Revision 42 to account for "
            "the temporal fluctuations caused by the recent hyper-lane expansion.\n\n"
            "Key Changes:\n"
            "1. The year now consists of 400 standard days.\n"
            "2. 'Zorblax' has been added as the 13th month.\n"
            "3. Leap seconds are now strictly prohibited to prevent spontaneous chronal implosions."
        )
    },
    {
        "filename": "Deep_Sea_Mining_Protocol.pdf",
        "title": "Deep Sea Mining Safety Protocol v1",
        "content": (
            "This protocol outlines the safety requirements for deep-sea mining operations in the "
            "Mariana Trench sector.\n\n"
            "Requirements:\n"
            "- All submersibles must be rated for 11,000 meters depth.\n"
            "- Personnel must undergo 4 weeks of high-pressure acclimatization.\n"
            "- Beware of giant squids: standard repellant must be deployed every 12 hours."
        )
    },
    {
        "filename": "Jurassic_Evacuation_Routes.pdf",
        "title": "Jurassic Park Evacuation Routes",
        "content": (
            "In the event of a dinosaur containment failure, immediately proceed to the nearest "
            "evacuation bunker.\n\n"
            "Routes:\n"
            "- Sector A (T-Rex Paddock): Follow the red flares to Bunker 1.\n"
            "- Sector B (Raptor Pen): Do not run. Walk slowly to Bunker 2.\n"
            "- Sector C (Triceratops Range): Wait for the armored transport."
        )
    },
    {
        "filename": "Time_Travel_Ethics.pdf",
        "title": "Time Travel Paradox Prevention Guide",
        "content": (
            "Time travel is a privilege, not a right. To prevent the collapse of reality, adhere "
            "to these ethical guidelines:\n\n"
            "1. Do not interact with your past self.\n"
            "2. Do not alter historical events prior to 1950.\n"
            "3. If you accidentally become your own grandparent, report to the Temporal "
            "Authority immediately for quantum untangling."
        )
    },
    {
        "filename": "Mars_Colony_Hydroponics.pdf",
        "title": "Mars Colony Hydroponics Manual",
        "content": (
            "Harvesting crops on Mars requires precise environmental control.\n\n"
            "Optimal Settings:\n"
            "- Humidity: 65%\n"
            "- Temperature: 22 degrees Celsius\n"
            "- Light Cycle: 16 hours on, 8 hours simulated darkness.\n\n"
            "Note: Martian soil supplements must be purified of perchlorates before use."
        )
    },
    {
        "filename": "Cybernetic_Maintenance.pdf",
        "title": "Cybernetic Implant Maintenance Manual",
        "content": (
            "Regular maintenance of your cybernetic enhancements ensures longevity and prevents "
            "spontaneous shutdown.\n\n"
            "Schedule:\n"
            "- Daily: Clean neural connection ports with a dry cloth.\n"
            "- Weekly: Run the internal diagnostic software (version 8.4 or higher).\n"
            "- Monthly: Replace servo fluids in mechanical limbs."
        )
    },
    {
        "filename": "Unicorn_Husbandry.pdf",
        "title": "Unicorn Husbandry Best Practices",
        "content": (
            "Caring for unicorns requires a delicate touch and a pure heart.\n\n"
            "Diet:\n"
            "- 50% enchanted oats.\n"
            "- 30% wild clover.\n"
            "- 20% rainbow-infused water.\n\n"
            "Warning: Never feed a unicorn after midnight or expose their horns to direct moonlight."
        )
    },
    {
        "filename": "Atlantis_Brochure.pdf",
        "title": "Atlantis Tourism Brochure",
        "content": (
            "Welcome to Atlantis, the jewel of the ocean floor!\n\n"
            "Attractions:\n"
            "- The Poseidon Arena: Watch the famous mermaid synchronized swimming team.\n"
            "- Coral Gardens: A serene park made entirely of bioluminescent coral.\n"
            "- Sub-Aqua Dining: Enjoy the finest kelp-based cuisine in the city.\n\n"
            "Remember to calibrate your gill-implants before arrival."
        )
    },
    {
        "filename": "Quantum_Teleportation.pdf",
        "title": "Quantum Teleportation Ethics Guidelines",
        "content": (
            "Teleportation involves the theoretical destruction and recreation of consciousness.\n\n"
            "Guidelines operators must follow:\n"
            "1. Operators must confirm the destination buffer is empty before initiating transport.\n"
            "2. If a fly enters the telepod, abort the sequence immediately.\n"
            "3. Retain a backup of the traveler's pattern for 72 hours in case of reconstruction errors."
        )
    },
    {
        "filename": "Dragon_Feeding_2050.pdf",
        "title": "Dragon Feeding Schedule 2050",
        "content": (
            "Official feeding schedule for the National Dragon Reserve.\n\n"
            "Schedule:\n"
            "- Fire Drakes: 50 sheep every Tuesday at noon.\n"
            "- Frost Wyrms: 2 tons of frozen fish every Thursday.\n"
            "- Acid Spitters: Chemical neutralizer pellets and sulfur cakes on weekends.\n\n"
            "Keep hands and flammable items away from the enclosures at all times."
        )
    }
]

for doc in documents:
    pdf = PDF()
    pdf.add_page()
    pdf.set_font("helvetica", "B", 18)
    pdf.cell(w=0, h=10, text=doc["title"], new_x="LMARGIN", new_y="NEXT", align="L")
    pdf.ln(10)
    
    pdf.set_font("helvetica", "", 12)
    clean_content = doc["content"].replace("—", "-").replace("’", "'")
    pdf.multi_cell(w=0, h=10, text=clean_content)
    
    pdf_path = os.path.join(pdf_dir, doc["filename"])
    pdf.output(pdf_path)
    print(f"Generated {pdf_path}")

print("All 10 completely unique, fictional PDFs generated successfully.")
