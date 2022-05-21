# GoTo London, a stupidly simple service (SSS)

`goto-london-sss` is a config-driven web app to facilitate snap decision-making about how to get to a destination of your choice in London.

It lets you configure a series of destinations (turned into server endpoints) and transport modalities, and based on live transit times from the TFL API GoTo will tell you how to get there fastest.

Instead of a fully-featured journey planner (boo! who wants those?), this takes hard-coded transit options you would consider for a particular destination, and just tells you which to take.

I, for example, can feasibly get to work by walking, bus, or tube (lucky me!). On any given day one of those might be faster/slower based on exactly when I want to leave the house. It also lets me plug my own estimate of exactly how long I need to (comfortably) make it onto any particular transport modality, which I find the "clever" apps still frankly struggle with. 

An example, as always, is most illustrative:

```yaml
# config.yaml.prod

# Configure an overall +/- cost per modality in minutes
# This is because I like walking, and that's worth time to me.
# I'd prefer to walk > bus > tube it!
walk_time_bonus: 3
bus_time_bonus: 0
tube_time_bonus: -5

# Define destinations. 
destinations:
  # define a destination. This will be set up as an endpoint on the server under <host>/goto/<destination>
  - kgx:
      bus:
        number: 390
        origin_stop_id: 73053  # Carleton Road
        destination_stop_id: 76007  # Kings X/St Pancras
        origin_walking_time: 2  # How long to get to bus stop
        destination_walking_time: 5  # How long from destination bus stop
      tube: 
        line: Northern
        origin_station: Kentish Town
        destination_station: Kings Cross
        origin_walking_time: 10  # How long to get on tube
        destination_walking_time: 5  # How long from tube
      walk:
        total_time: 30
```
