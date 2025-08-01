# models/database.py
from sqlalchemy import create_engine, Column, Integer, String, DateTime, ForeignKey, JSON, Boolean, Text, text, DECIMAL
from sqlalchemy.orm import sessionmaker, scoped_session, declarative_base, relationship
from sqlalchemy.engine import Engine
from sqlalchemy.pool import QueuePool
from contextlib import contextmanager
from datetime import datetime
import logging
from ..config import Config
import os
from dotenv import load_dotenv
load_dotenv()

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create declarative base
Base = declarative_base()

# Configure engine with optimized settings for Supabase
engine = create_engine(
    Config.DATABASE_URL,
    pool_pre_ping=True,  # Check connection before using
    pool_recycle=180,    # Recycle connections every 3 minutes
    pool_size=3,         # Smaller pool size to prevent exhaustion
    max_overflow=5,      # Allow some overflow for peak times
    pool_timeout=10,     # Timeout after 10 seconds
    pool_use_lifo=True,  # Use LIFO to reduce number of connections in use
    connect_args={
        "connect_timeout": 5,  # Connection timeout after 5 seconds
        "application_name": "flex-warranty-api",  # Help identify connections in Supabase
        "options": "-c statement_timeout=5000",  # 5 second statement timeout
        "sslmode": "require",  # Force SSL connection
        "gssencmode": "disable",  # Disable GSSAPI encryption
        "target_session_attrs": "read-write"  # Ensure we connect to a writable instance
    }
)

# Create session factory with shorter timeout
SessionFactory = sessionmaker(
    bind=engine,
    expire_on_commit=False,  # Prevent expired object issues
    autocommit=False,
    autoflush=False
)

# Use scoped session with proper cleanup
Session = scoped_session(SessionFactory)

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

@contextmanager
def get_db():
    db = Session()
    try:
        yield db
        db.commit()
    except Exception as e:
        logger.error(f"Database error: {str(e)}")
        db.rollback()
        raise
    finally:
        db.close()
        Session.remove()


class Shop(Base):
    __tablename__ = 'shops'

    id = Column(Integer, primary_key=True)
    shop_url = Column(String(255), unique=True, nullable=False)
    access_token = Column(String(255))
    api_key = Column(String(255))  # API key for authenticating API calls
    product_id = Column(String(255))  # Shopify product ID for warranty product
    variant_id = Column(String(255))  # Shopify variant ID for warranty product
    collection_id = Column(String(255))  # Shopify collection ID for "All" collection
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    offers = relationship('Offer', back_populates='shop')
    themes = relationship('OfferTheme', back_populates='shop')
    layouts = relationship('OfferLayout', back_populates='shop')
    settings = relationship('ShopSettings', back_populates='shop', uselist=False)


class ShopSettings(Base):
    __tablename__ = 'shop_settings'

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    show_offer_on_checkout = Column(Boolean, default=True)
    show_email_optin = Column(Boolean, default=True)
    api_token = Column(String(255))
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shop = relationship('Shop', back_populates='settings')


class Offer(Base):
    __tablename__ = 'offers'

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    headline = Column(Text)
    body = Column(Text)
    image_url = Column(Text)
    button_text = Column(String(255))
    button_url = Column(Text)
    theme = Column(JSON)  # Stores theme settings
    layout_id = Column(Integer, ForeignKey('offer_layouts.id'))
    status = Column(String(50), default='active')  # active, inactive, draft
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    shop = relationship('Shop', back_populates='offers')
    layout = relationship('OfferLayout')


class OfferTheme(Base):
    __tablename__ = 'offer_themes'

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    name = Column(String(255), nullable=False)
    primary_color = Column(String(50))
    secondary_color = Column(String(50))
    accent_color = Column(String(50))
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship('Shop', back_populates='themes')


class OfferLayout(Base):
    __tablename__ = 'offer_layouts'

    id = Column(Integer, primary_key=True)
    shop_id = Column(Integer, ForeignKey('shops.id'), nullable=False)
    name = Column(String(255))
    description = Column(Text)
    css_classes = Column(Text)
    preview_html = Column(Text)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    shop = relationship('Shop', back_populates='layouts')


class WarrantyInsuranceProduct(Base):
    __tablename__ = 'warranty_insurance_products'

    id = Column(Integer, primary_key=True)
    insurer_name = Column(String(100), nullable=False)  # e.g., 'AIG', 'SquareTrade', etc.
    product_category = Column(String(100), nullable=False)  # e.g., 'Consumer Electronics', 'Desktops, Laptops', 'Tablets', 'TVs'
    includes_adh = Column(Boolean, default=False)  # Accidental Damage from Handling
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    pricing_bands = relationship('WarrantyPricingBand', back_populates='insurance_product')


class WarrantyPricingBand(Base):
    __tablename__ = 'warranty_pricing_bands'

    id = Column(Integer, primary_key=True)
    insurance_product_id = Column(Integer, ForeignKey('warranty_insurance_products.id'), nullable=False)
    msrp_min = Column(DECIMAL(10, 2), nullable=False)
    msrp_max = Column(DECIMAL(10, 2), nullable=False)
    price_2_year = Column(DECIMAL(10, 2), nullable=False)
    price_3_year = Column(DECIMAL(10, 2), nullable=False)
    effective_date = Column(DateTime, nullable=False, default=datetime.utcnow)
    expiry_date = Column(DateTime)  # NULL means currently active
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    insurance_product = relationship('WarrantyInsuranceProduct', back_populates='pricing_bands')


# Initialize database
def init_db():
    Base.metadata.create_all(bind=engine) 