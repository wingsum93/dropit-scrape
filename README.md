# dropit website price scrapping
For user to fetch website product and price



## how to setup virtual environment

```sh
python -m venv .venv
source .venv/bin/activate  # Windows 用 .venv\Scripts\activate
```


### Install Lib (win)
```sh
pip install -r requirements.txt
```


### Init postgresdb
```shell
python -m scraper.db.product_repo
```

## Run the proj.
### Fetch all product from category
```shell
python -m scraper.main
```

### fetch Product Items
```shell
python -m scraper.fetch_product_price
```





# Installation
Install python 3
Install ![Warp](https://www.warp.dev/)
Install postgres db (optional)
    Can be from container / install for machine





# Goal of the project
Fetch all items from the Devonshire Shop

### API for fetch 24-96 products
https://api.freshop.ncrcloud.com/1/products?app_key=lindos&department_id=22886618&department_id_cascade=true&fields=id%2Cidentifier%2Cattribution_token%2Creference_id%2Creference_ids%2Cupc%2Cname%2Cstore_id%2Cdepartment_id%2Csize%2Ccover_image%2Cprice%2Csale_price%2Csale_price_md%2Csale_start_date%2Csale_finish_date%2Cprice_disclaimer%2Csale_price_disclaimer%2Cis_favorite%2Crelevance%2Cpopularity%2Cshopper_walkpath%2Cfulfillment_walkpath%2Cquantity_step%2Cquantity_minimum%2Cquantity_initial%2Cquantity_label%2Cquantity_label_singular%2Cvarieties%2Cquantity_size_ratio_description%2Cstatus%2Cstatus_id%2Csale_configuration_type_id%2Cfulfillment_type_id%2Cfulfillment_type_ids%2Cother_attributes%2Cclippable_offer%2Cslot_message%2Ccall_out%2Chas_featured_offer%2Ctax_class_label%2Cpromotion_text%2Csale_offer%2Cstore_card_required%2Caverage_rating%2Creview_count%2Clike_code%2Cshelf_tag_ids%2Coffers%2Cis_place_holder_cover_image%2Cvideo_config%2Cenforce_product_inventory%2Cdisallow_adding_to_cart%2Csubstitution_type_ids%2Cunit_price%2Coffer_sale_price%2Ccanonical_url%2Coffered_together%2Csequence&include_offered_together=true&limit=96&popularity_sort=asc&render_id=1769356302366&sort=popularity&store_id=7442&token=6bd97c7e8e26c61b3fb35ad0320d50f0

## current issue
All product is around 13,628 items

But if we go to produc detail website, it take serval second to fetch data. So it take up to 5~6 second to fetch 1 product. The overall process take 68140 second (18.92 hours)
