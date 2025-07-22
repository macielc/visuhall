import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base, Product, Location, PickingOrder, OrderItem

# --- Configuração do Banco de Dados ---
db_user = os.getenv('POSTGRES_USER')
db_password = os.getenv('POSTGRES_PASSWORD')
db_name = os.getenv('POSTGRES_DB')
db_host = 'db' # Nome do serviço do container do DB

DATABASE_URL = f"postgresql://{db_user}:{db_password}@{db_host}:5432/{db_name}"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# --- Criação das Tabelas ---
# Esta é a maneira correta de garantir que as tabelas existam.
# Deve ser executado como um passo de setup, não no app principal.
print("Criando tabelas no banco de dados, se não existirem...")
Base.metadata.create_all(bind=engine)
print("Tabelas criadas com sucesso.")

# --- Povoamento do Banco de Dados ---
db = SessionLocal()

try:
    # Limpa dados existentes para evitar duplicatas
    db.query(OrderItem).delete()
    db.query(PickingOrder).delete()
    db.query(Location).delete()
    db.query(Product).delete()
    db.commit()
    print("Dados antigos limpos com sucesso.")

    # Produtos do PDF 1
    p1 = Product(sku="58363", name="CBEM D/COL BDY SPLSH NUV/ALEG 200ml")
    p2 = Product(sku="84391", name="MALBEC DES COL GOLD V3 100ml")
    p3 = Product(sku="81634", name="MAKE B BASE LIQ RETIN H 15 26g")
    p4 = Product(sku="82961", name="FLAC OUI EDP MADELEINE 862 3x1ml")

    # Produtos do PDF 2
    p5 = Product(sku="70693", name="SOPHIE LOC HID CPO 200ml")
    p6 = Product(sku="04510", name="REF BOTIK CR FAC FIRM AC/HIALUR 40g")
    p7 = Product(sku="82686", name="EGEO DES COL BLUE C/CAR 90ml")
    p8 = Product(sku="55648", name="MEN DES COL NBA 100ml")
    p9 = Product(sku="86868", name="CLASH CR PRE E POS BARBA 150g")
    p10 = Product(sku="53677", name="QUASAR CR P/ BARB BLUE 110g")
    p11 = Product(sku="50820", name="QUASAR DES COL RUSH V2 100ml")
    p12 = Product(sku="48141", name="ACCORDES DES COL 80ml V5")
    p13 = Product(sku="74043", name="LINDA DES COL V4 100ml")
    p14 = Product(sku="48139", name="COFFEE DES COL WOMAN SEDUC 100ml V5")
    p15 = Product(sku="76700", name="LIZ DES COL 100ml")
    p16 = Product(sku="47339", name="LIZ DES COL SUBLIME 100ml")
    p17 = Product(sku="82688", name="EGEO DES COL DOLCE C/CAR 90ml")
    p18 = Product(sku="77183", name="LIZ CREM DES HID CPO 250g")
    p19 = Product(sku="01302", name="PMPCK LILY DES ANTIT AER 2x75g")
    
    db.add_all([p1, p2, p3, p4, p5, p6, p7, p8, p9, p10, p11, p12, p13, p14, p15, p16, p17, p18, p19])
    db.commit()

    # Localizações do PDF 1
    l1 = Location(rua=1, rack_number=7, linha=5, coluna='A', product_id=p1.id)
    l2 = Location(rua=2, rack_number=2, linha=5, coluna='D', product_id=p2.id)
    l3 = Location(rua=4, rack_number=1, linha=8, coluna='E', product_id=p3.id)
    l4 = Location(rua=5, rack_number=1, linha=1, coluna='B', product_id=p4.id)

    # Localizações do PDF 2
    l5 = Location(rua=1, rack_number=2, linha=2, coluna='C', product_id=p5.id)
    l6 = Location(rua=1, rack_number=3, linha=3, coluna='F', product_id=p6.id)
    l7 = Location(rua=2, rack_number=1, linha=4, coluna='C', product_id=p7.id)
    l8 = Location(rua=2, rack_number=1, linha=4, coluna='E', product_id=p8.id)
    l9 = Location(rua=2, rack_number=2, linha=2, coluna='E', product_id=p9.id)
    l10 = Location(rua=2, rack_number=4, linha=3, coluna='D', product_id=p10.id)
    l11 = Location(rua=2, rack_number=4, linha=4, coluna='A', product_id=p11.id)
    l12 = Location(rua=2, rack_number=5, linha=2, coluna='A', product_id=p12.id)
    l13 = Location(rua=2, rack_number=7, linha=3, coluna='C', product_id=p13.id)
    l14 = Location(rua=2, rack_number=9, linha=4, coluna='A', product_id=p14.id)
    l15 = Location(rua=2, rack_number=10, linha=3, coluna='A', product_id=p15.id)
    l16 = Location(rua=2, rack_number=10, linha=3, coluna='C', product_id=p16.id)
    l17 = Location(rua=2, rack_number=10, linha=4, coluna='B', product_id=p17.id)
    l18 = Location(rua=2, rack_number=10, linha=5, coluna='G', product_id=p18.id)
    l19 = Location(rua=3, rack_number=1, linha=2, coluna='B', product_id=p19.id)

    db.add_all([l1, l2, l3, l4, l5, l6, l7, l8, l9, l10, l11, l12, l13, l14, l15, l16, l17, l18, l19])
    db.commit()
        
    print("Banco de dados populado com TODOS os itens dos PDFs de teste!")

finally:
    db.close()

# A função seed_database() não existe mais, o script agora é executado diretamente.
# if __name__ == "__main__":
#     seed_database() 