from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.sql import func

Base = declarative_base()

class Product(Base):
    __tablename__ = 'products'
    id = Column(Integer, primary_key=True)
    sku = Column(String(80), unique=True, nullable=False)
    name = Column(String(120), nullable=False)
    locations = relationship('Location', backref='product', lazy='subquery')
    order_items = relationship('OrderItem', backref='product', lazy='subquery')


class Location(Base):
    __tablename__ = 'locations'
    id = Column(Integer, primary_key=True)
    rua = Column(Integer, nullable=False)
    rack_number = Column(Integer, nullable=False)
    linha = Column(Integer, nullable=False)
    coluna = Column(String(5), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=True)

    def get_address_str(self):
        return f"RUA {self.rua} / Rack {self.rack_number} / {self.linha} / {self.coluna}"


class PickingOrder(Base):
    __tablename__ = 'picking_orders'
    id = Column(Integer, primary_key=True)
    created_at = Column(DateTime, server_default=func.now())
    status = Column(String(20), default='pending')
    items = relationship('OrderItem', backref='order', lazy='subquery', cascade="all, delete-orphan")


class OrderItem(Base):
    __tablename__ = 'order_items'
    id = Column(Integer, primary_key=True)
    picking_order_id = Column(Integer, ForeignKey('picking_orders.id'), nullable=False)
    product_id = Column(Integer, ForeignKey('products.id'), nullable=False)
    location_id = Column(Integer, ForeignKey('locations.id'), nullable=False)
    quantity = Column(Integer, nullable=False)
    status = Column(String(20), default='pending') # pending, picked, skipped

    location = relationship('Location', lazy='joined') 