def get_cast(soup_object):
    cast = []
    actors = soup_object.find_all("div", {"class":"title-credits__actor"})
    for actor in actors:
        actor_name = actor.text.replace('\n',"")
        cast.append(actor_name)
    return cast