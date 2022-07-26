from usrlib.rdb.config.setting import Base, session
from sqlalchemy import Column, String, DateTime
from sqlalchemy.sql import func
from sqlalchemy.exc import SQLAlchemyError


class ProductData(Base):
    """
    product_data Model
    """
    __tablename__ = 'product_data'
    asin = Column(String(50), primary_key=True)
    name = Column(String(255))
    brand = Column(String(50))
    manufacturer = Column(String(50))
    created_at = Column(DateTime, default=func.now())
    updated_at = Column(DateTime, default=func.now(), onupdate=func.now())

    def insert_product_data(
        asin: str, name: str, brand: str, manufacturer: str
    ):
        """
        product data登録
        Parameters
        ----------
        asin : str
            ASIN
        name : str
            製品名
        brand : str
            ブランド
        manufacturer : str
            メーカー
        Returns
        -------
        insert result : boolean
            登録結果
        """
        try:
            regist_data = ProductData(
                asin=asin, name=name, brand=brand, manufacturer=manufacturer
            )
            print(f"regist data:asin={asin}, brand={brand}, manufacturer={manufacturer}")
            session.add(regist_data)
            session.commit()
            return True
        except SQLAlchemyError:
            session.rollback()

    def update_product_data(
        asin: str, name: str, brand: str, manufacturer: str
    ):
        """
        product data更新
        Parameters
        ----------
        asin : str
            ASIN
        name : str
            製品名
        brand : str
            ブランド
        manufacturer : str
            メーカー
        Returns
        -------
        update result : boolean
            登録結果
        """
        try:
            print(f"update data:asin={asin}, brand={brand}, manufacturer={manufacturer}")

            query = session.query(ProductData)
            product_data_update = query.filter(ProductData.asin == asin).first()
            product_data_update.name = name
            product_data_update.brand = brand
            product_data_update.manufacturer = manufacturer

            session.commit()
            return True
        except SQLAlchemyError:
            session.rollback()

    def get_product_data(asin: str):
        """
        product data取得(ASIN)

        Parameters
        ----------
        asin : str
            ASIN

        Returns
        -------
        登録あり：product_data model
        登録なし：False
        """
        result_product = session.query(ProductData).get(asin)
        if result_product is not None:
            return result_product
        return False
