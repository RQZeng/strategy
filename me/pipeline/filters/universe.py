# -*- coding: utf-8 -*-
"""
Created on Wed May 17 13:19:27 2017

@author: kanghua
"""

import pandas as pd
import numpy as np
import math

from zipline.api import (
    symbol,
    sid,
)

from zipline.pipeline.data import USEquityPricing
from zipline.pipeline.factors import AverageDollarVolume, CustomFactor
from zipline.pipeline.filters import CustomFilter

from me.pipeline.utils.tushare import load_tushare_df
from me.pipeline.classifiers.tushare.sector import getSector,getSectorSize,industryClassied

market_cap_limit = 1#yi

# Average Dollar Volume without nanmean, so that recent IPOs are truly removed
class ADV_adj(CustomFactor):
    inputs = [USEquityPricing.close, USEquityPricing.volume]
    window_length = 252
    def compute(self, today, assets, out, close, volume):
        close[np.isnan(close)] = 0
        out[:] = np.mean(close * volume, 0)

def getMarketCap():
    print("==enter getMarketCap==")
    info=load_tushare_df("basic") 
    class MarketCap(CustomFactor):
        # Shares Outstanding  
        inputs = [USEquityPricing.close]
        window_length = 1    
        def outstanding(self,assets):
            oslist=[]
            for msid in assets:
                stock = sid(msid).symbol
                try:
                    os = info.ix[stock]['outstanding']
                    oslist.append(os)
                except:
                    oslist.append(0)
                else:
                    pass
            return oslist
        def compute(self, today, assets, out, close):
            out[:] =   close[-1] * self.outstanding(assets)
    return MarketCap()
     
 
def IsInSymbolsList(sec_list):  
    '''Returns a factor indicating membership (=1) in the given iterable of securities'''  
    print("==enter IsInSymbolsList==")
    class IsInSecListFactor(CustomFilter):  
        inputs = [];  
        window_length = 1
        def compute(self, today, asset_ids, out, *inputs):
            out[:] = asset_ids.isin(sec_list)  
    return IsInSecListFactor()  


def universe_filter():
    """
    Create a Pipeline producing Filters implementing common acceptance criteria.
    
    Returns
    -------
    zipline.Filter
        Filter to control tradeablility
    """
    
    a_stocks=[]
    info=load_tushare_df("basic") 
    sme =load_tushare_df("sme")
    gem =load_tushare_df("gem")
    st  =load_tushare_df("st")
    uset = pd.concat([sme,gem,st])
    newset=info.drop([y for y in uset['code'] ],axis=0)
    for EachStockID in newset.index:
        a_stocks.append(EachStockID)
    print("test ... ",)
    sec_list=[]
    for y in a_stocks:
        try:
            sid = symbol(y).sid
        except:
            pass
        else:    
            sec_list.append(sid)    
    print("---sec_list:",sec_list)    
    mySymbolsListfiter = IsInSymbolsList(sec_list)
    
    # Equities with an average daily volume greater than 5000000.
    high_volume = (AverageDollarVolume(window_length=252) > 5000000)
    liquid = ADV_adj() > 2500000
    market_cap_filter = getMarketCap() > market_cap_limit
    universe_filter = (mySymbolsListfiter & market_cap_filter & liquid & high_volume)
    return universe_filter

def sector_filter(tradeable_count, sector_exposure_limit):
    """
    Mask for Pipeline in create_tradeable. Limits each sector so as not to be over-exposed

    Parameters
    ----------
    tradeable_count : int
        Target number of constituent securities in universe
    sector_exposure_limit: float
        Target threshold for any particular sector
    Returns
    -------
    zipline.Filter
        Filter to control sector exposure
    """
    
    g_inds = industryClassied()
    #print("g_inds",g_inds)
    sector = getSector(g_inds)
    # set thresholds
    if sector_exposure_limit < ((1. / getSectorSize())):
        threshold = int(math.ceil((1. / getSectorSize()) * tradeable_count))
    elif sector_exposure_limit > 1.:
        threshold = tradeable_count
    else:
        threshold = int(math.ceil(sector_exposure_limit * tradeable_count))
   
    transport_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['交通运输'.decode("UTF-8")]))             #
    instrument_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['仪器仪表'.decode("UTF-8")]))
    media_entertainment_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['传媒娱乐'.decode("UTF-8")]))   #
    water_supply_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['供水供气'.decode("UTF-8")]))          #
    highway_bridge_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['公路桥梁'.decode("UTF-8")]))        #
    other_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['其它行业'.decode("UTF-8")]))
    animal_husbandry_fishery_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['农林牧渔'.decode("UTF-8")]))  #
    pesticide_fertilizer_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['农药化肥'.decode("UTF-8")]))
    chemical_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['化工行业'.decode("UTF-8")]))                  #
    chemical_fiber_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['化纤行业'.decode("UTF-8")]))
    medical_device_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['医疗器械'.decode("UTF-8")]))
    printing_packaging_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['印刷包装'.decode("UTF-8")]))
    power_plant_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['发电设备'.decode("UTF-8")]))
    business_department_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['商业百货'.decode("UTF-8")]))       #
    plastics_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['塑料制品'.decode("UTF-8")]))
    furniture_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['家具行业'.decode("UTF-8")]))                 #
    appliance_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['家电行业'.decode("UTF-8")]))                 #
    building_materials_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['建筑建材'.decode("UTF-8")]))        #
    development_zone_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['开发区'.decode("UTF-8")]))
    real_estate_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['房地产'.decode("UTF-8")]))                #
    motorcycle_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['摩托车'.decode("UTF-8")]))
    nonferrous_metals_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['有色金属'.decode("UTF-8")]))         #
    clothing_footwear_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['服装鞋类'.decode("UTF-8")]))         #
    machinery_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['机械行业'.decode("UTF-8")]))                 #
    time_shares_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['次新股'.decode("UTF-8")]))
    cement_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['水泥行业'.decode("UTF-8")]))
    automobile_manufacturing_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['汽车制造'.decode("UTF-8")]))  #
    coal_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['煤炭行业'.decode("UTF-8")]))                      #
    material_trade_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['物资外贸'.decode("UTF-8")]))
    environmental_protection_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['环保行业'.decode("UTF-8")]))   #
    glass_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['玻璃行业'.decode("UTF-8")]))
    biopharmaceuticals_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['生物制药'.decode("UTF-8")]))         #
    power_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['电力行业'.decode("UTF-8")]))                     
    electronic_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['电器行业'.decode("UTF-8")]))
    electronic_information_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['电子信息'.decode("UTF-8")]))     #
    electronic_device_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['电子器件'.decode("UTF-8")]))            
    oil_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['石油行业'.decode("UTF-8")]))                     
    textile_machinery_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['纺织机械'.decode("UTF-8")]))
    textile_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['纺织行业'.decode("UTF-8")]))
    integrated_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['综合行业'.decode("UTF-8")]))
    ship_manufacturing_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['船舶制造'.decode("UTF-8")]))
    paper_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['造纸行业'.decode("UTF-8")]))
    hotel_tour_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['酒店旅游'.decode("UTF-8")]))                #
    wine_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['酿酒行业'.decode("UTF-8")]))
    financial_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['金融行业'.decode("UTF-8")]))                 #
    steel_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['钢铁行业'.decode("UTF-8")]))                     #      
    ceramics_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['陶瓷行业'.decode("UTF-8")]))           
    aircraft_manufacturing_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['飞机制造'.decode("UTF-8")]))
    food_industry_trim = AverageDollarVolume(window_length=21).top(threshold, mask=sector.eq(g_inds['食品行业'.decode("UTF-8")]))             #
    
    
    return transport_trim|media_entertainment_trim|\
           chemical_trim|medical_device_trim|\
           power_plant_trim|business_department_trim|appliance_trim|\
           building_materials_trim|real_estate_trim|nonferrous_metals_trim|\
           clothing_footwear_trim|machinery_trim|automobile_manufacturing_trim|\
           coal_trim|environmental_protection_trim|biopharmaceuticals_trim|\
           power_trim|electronic_information_trim|electronic_device_trim|\
           oil_trim|textile_trim|hotel_tour_trim|\
           wine_trim|financial_trim|steel_trim|\
           aircraft_manufacturing_trim|food_industry_trim
     
        