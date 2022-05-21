# GoTo London, a stupidly simple service (SSS)

`goto-london-sss` is a config-driven web app to facilitate snap decision-making about how to get to a destination of your choice in London.

It lets you configure a series of endpoints and transport modalities, and based on live transit times from the TFL API will tell you how to get there fastest.

Instead of a fully-featured journey planner (boo), this takes hard-coded transit options you would consider for a particular destination, and just tells you which to take.

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
    bus_number: 390
    bus_from_stop_id: 73053  # Carleton Road
    bus_to_stop_id: 76007  # Kings X/St Pancras
    bus_from_walking_time: 2  # How long to get to bus stop
    bus_to_walking_time: 5  # How long from destination bus stop
    tube_line: Northern
    tube_from_station: Kentish Town
    tube_to_station: Kings Cross
    tube_from_walking_time: 10  # How long to get on tube
    tube_to_walking_time: 5  # How long from tube
    walk_there_time: 30
```
