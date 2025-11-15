from django.db import models

class ProductPrice(models.Model):
    PRODUCT_CHOICES = [
        ('1', 'abshode_naghd_farda'),
        ('2', 'abshode_naghd_pasfarda'),
        ('3', 'abshode_with_gateway'),
        ('4', 'seke_nim_1386'),
        ('5', 'seke_nim_sal_payeen_ta_80'),
        ('6', 'seke_rob_1386'),
        ('7', 'seke_rob_1403'),
        ('8', 'seke_rob_sal_payeen_ta_80'),
        ('9', 'seke_tamam_1386'),
        ('10', 'seke_tamam_1403'),
        ('11', 'seke_tamam_sal_payeen'),
        

    ]
    product=models.CharField(
        max_length=2,
        choices=PRODUCT_CHOICES
        )
    base_price_sell=models.BigIntegerField(default=0)
    base_price_buy=models.BigIntegerField(default=0)
    time = models.TimeField(auto_now=True)
    is_exist=models.BooleanField(default=True)

    def __str__(self):
        return dict(self.PRODUCT_CHOICES).get(self.product, self.product)
