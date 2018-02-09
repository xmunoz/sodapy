
# coding: utf-8

# # Example 02: SoSQL Queries
# 
# This notebook discusses how to make more specific data requests, conserving your bandwith and  computational resources

# ## Setup

# In[3]:


import os
# Note that we don't need Pandas. 
# Filters allow you to accomplish many basic operations automatically

from sodapy import Socrata


# ## Find Some Data
# 
# As in the first example, I'm using the Santa Fe political contribution dataset
# 
# `https://opendata.socrata.com/dataset/Santa-Fe-Contributors/f92i-ik66.json`

# In[7]:


socrata_domain = 'opendata.socrata.com'
socrata_dataset_identifier = 'f92i-ik66'

# If you choose to use a token, run the following command on the terminal (or add it to your .bashrc)
# $ export SODAPY_APPTOKEN=<token>
try:
    socrata_token = os.environ['SODAPY_APPTOKEN']
except:
    socrata_token = None


# In[8]:


client = Socrata(socrata_domain, socrata_token)


# ## Use Metadata to Plan Your Query
# You've probably looked through the column names and descriptions in the web UI, 
# but it can be nice to have them right in your workspace as well.

# In[9]:


metadata = client.get_metadata(socrata_dataset_identifier)
[x['name'] for x in metadata['columns']]


# In[11]:


meta_amount = [x for x in metadata['columns'] if x['name'] == 'AMOUNT'][0]
meta_amount


# ## Efficiently Query for Data

# ### Restrict rows to above-average donations

# In[14]:


# Get the average from the metadata. Note that it's a string by default
meta_amount['cachedContents']['average']


# In[17]:


# Use the 'where' argument to filter the data before downloading it
results = client.get(socrata_dataset_identifier, where="amount >= 2433")
print("Total number of non-null results: {}".format(meta_amount['cachedContents']['non_null']))
print("Number of results downloaded: {}".format(len(results)))
results[:3]


# ### Restrict columns and order rows
# Often, you know which columns you want, so you can further simplify the download.
# 
# It can also be valuable to have results in order, so that you can quickly grab the 
# largest or smallest.

# In[19]:


results = client.get(socrata_dataset_identifier, 
                     where="amount < 2433", 
                     select="amount, job",
                     order="amount ASC")
results[:3]


# ### Conduct basic analytic operations
# You can even accomplish some basic analytics operations like finding sums.
# 
# If you're planning on doing further processing, note that the numeric outputs 
# are strings by default

# In[20]:


results = client.get(socrata_dataset_identifier, 
                     group="recipient", 
                     select="sum(amount), recipient", 
                     order="sum(amount) DESC")
results


# ### Break download into managable chunks
# Sometimes you do want all the data, but it would be too big for one download. 
# 
# By default, all queries have a limit of 1000 rows, but you can manually set it 
# higher or lower. If you want to loop through results, just use `offset`

# In[26]:


results = client.get(socrata_dataset_identifier, limit=6, select="name, amount")
results


# In[30]:


loop_size = 3
num_loops = 2

for i in range(num_loops):
    results = client.get(socrata_dataset_identifier, 
                         select="name, amount", 
                         limit=loop_size,
                         offset=loop_size*i)
    print("\n> Loop number: {}".format(i))
    
    # This simply formats the output nicely
    for result in results:
        print(result)


# ### Free text search
# This will be more valuable in datasets with many string columns, since we're talking about
# politics, it seems reasonable to see whether Washington shows up anywhere

# In[39]:


results = client.get(socrata_dataset_identifier, q="Washington")
results[0]


# ### Query strings
# All of the queries above were made with method parameters, 
# but you could also pass all the parameters at once in a 
# SQL-like format

# In[40]:


query = """
select 
    name, 
    amount
where
    amount > 1000
    and amount < 2000
limit
    5
"""

results = client.get(socrata_dataset_identifier, query=query)
results


# That's it! For more background, check out [Queries using SODA](https://dev.socrata.com/docs/queries/). 
