class Polozka:
    def __init__(self, nazev, cena):
        self.nazev = nazev
        self.cena = cena

class Uctenka:
    def __init__(self):
        self.polozky = []

    def pridej_polozku(self, polozka):
        self.polozky.append(polozka)

    