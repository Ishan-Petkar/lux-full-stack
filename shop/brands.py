"""Maison facts shown on product pages: country and year founded (public knowledge; verify before any commercial use)."""

BRANDS = {
    "A. Lange & Söhne": ("Germany", 1845), "Audemars Piguet": ("Switzerland", 1875), "Barbour": ("United Kingdom", 1894),
    "Balenciaga": ("Spain / France", 1919), "Berluti": ("France", 1895), "Bottega Veneta": ("Italy", 1966),
    "Breitling": ("Switzerland", 1884), "Brioni": ("Italy", 1945), "Brunello Cucinelli": ("Italy", 1978), "Bulgari": ("Italy", 1884),
    "Burberry": ("United Kingdom", 1856), "Byredo": ("Sweden", 2006), "Canada Goose": ("Canada", 1957), "Cartier": ("France", 1847),
    "Chanel": ("France", 1910), "Chopard": ("Switzerland", 1860), "Christian Louboutin": ("France", 1991), "Church's": ("United Kingdom", 1873),
    "Common Projects": ("Italy / United States", 2004), "Creed": ("United Kingdom / France", 1760), "David Yurman": ("United States", 1980),
    "Dior": ("France", 1946), "Dunhill": ("United Kingdom", 1893), "Ermenegildo Zegna": ("Italy", 1910), "Fendi": ("Italy", 1925),
    "Giorgio Armani": ("Italy", 1975), "Globe-Trotter": ("United Kingdom", 1897), "Golden Goose": ("Italy", 2000), "Goyard": ("France", 1792),
    "Gucci": ("Italy", 1921), "Hermès": ("France", 1837), "Hublot": ("Switzerland", 1980), "IWC": ("Switzerland", 1868),
    "Jaeger-LeCoultre": ("Switzerland", 1833), "Jimmy Choo": ("United Kingdom", 1996), "John Lobb": ("United Kingdom", 1849),
    "Le Labo": ("United States", 2006), "Loro Piana": ("Italy", 1924), "Louis Vuitton": ("France", 1854), "Maison Francis Kurkdjian": ("France", 2009),
    "Maison Margiela": ("France", 1988), "Manolo Blahnik": ("United Kingdom", 1971), "Max Mara": ("Italy", 1951), "Mikimoto": ("Japan", 1893),
    "Moncler": ("France / Italy", 1952), "Montblanc": ("Germany", 1906), "Oliver Peoples": ("United States", 1987), "Omega": ("Switzerland", 1848),
    "Panerai": ("Italy / Switzerland", 1860), "Parker": ("United States", 1888), "Patek Philippe": ("Switzerland", 1839), "Pelikan": ("Germany", 1838),
    "Persol": ("Italy", 1917), "Piaget": ("Switzerland", 1874), "Prada": ("Italy", 1913), "Ralph Lauren Purple Label": ("United States", 1967),
    "Ray-Ban": ("United States", 1937), "Rimowa": ("Germany", 1898), "Rolex": ("Switzerland", 1905), "Saint Laurent": ("France", 1961),
    "Salvatore Ferragamo": ("Italy", 1927), "Smythson": ("United Kingdom", 1887), "TAG Heuer": ("Switzerland", 1860), "Tiffany & Co.": ("United States", 1837),
    "Tom Ford": ("United States", 2005), "Vacheron Constantin": ("Switzerland", 1755), "Valentino": ("Italy", 1960), "Van Cleef & Arpels": ("France", 1906),
    "Visconti": ("Italy", 1988), "Yves Saint Laurent": ("France", 1961), "Zenith": ("Switzerland", 1865), "Guerlain": ("France", 1828),
}


def facts(brand: str) -> str:
    c = BRANDS.get(brand)
    return f"{c[0]} · est. {c[1]}" if c else ""
