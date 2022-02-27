# coding=utf-8"""Function used to compute interests"""import randomfrom typing import Dictfrom building_seeding import BUILDING_ENCYCLOPEDIA, BuildingType, Parcelfrom building_seeding.district.districts import Districtsfrom building_seeding.interest import *from building_seeding.interest.density import densityfrom terrain import TerrainMapsfrom terrain.road_network import *class InterestSeeder:    """    Stores an InterestMap for each BuildingType and contains methods relative to seeding building types    """    def __init__(self, maps: TerrainMaps, districts: Districts, parcel_list: List[Parcel], scenario: str):        self.__terrain_maps = maps        self.__districts = districts        self.__interest_maps = dict()  # type: Dict[BuildingType, InterestMap]        self.__parcels = parcel_list        self.__scenario = scenario    def __getitem__(self, item):        if isinstance(item, BuildingType):            if item not in self.__interest_maps:                self.__interest_maps[item] = InterestMap(item, self.__scenario, self.__terrain_maps, self.__districts)            return self.__interest_maps[item]        elif type(item) == object:            raise TypeError("Expected BuildingType, found {} of class {}", item, item.__class__)        raise TypeError("Expected BuildingType, found {} of type {}", item, type(item))    def get_seed(self, building_type):        typed_interest_map = self[building_type]        typed_interest_map.update(self.__parcels)        seed, interest = None, -1        for _ in range(SEED_COUNT):            potential_seed = self.__districts.seed()            if ObstacleMap().is_accessible(potential_seed):                potential_interest = typed_interest_map.get_interest(potential_seed)                if seed is None or potential_interest > interest:                    seed, interest = potential_seed, potential_interest        if seed is None:            percentile = 95            while percentile >= 30:                potential_seed = typed_interest_map.get_seed(perc=percentile)                if potential_seed is None or ObstacleMap().is_accessible(potential_seed):                    return potential_seed                percentile -= 5            return None        return seed    def try_to_reuse_existing_parcel(self, new_type) -> BuildingType:        """        Replaces the type of an existing parcel with the type we're seeding if it increases its interest        :param new_type: type of the building we're seeding        :return: the type to seed        """        parcels = [_ for _ in self.__parcels if _.building_type != BuildingType.ghost and _.building_type != new_type]        if len(parcels) > REPLACE_PARCEL_TYPE_EXPLORATION:            parcels = random.sample(parcels, REPLACE_PARCEL_TYPE_EXPLORATION)        for parcel in parcels:            cur_type = parcel.building_type            # For every parcel of a different type than the one to be seeded, compute interest in changing type            seed = parcel.center            other_parcels = list(filter(lambda p: p != parcel, self.__parcels))            if not other_parcels:                continue            # Using sociability computed from the other placed parcels, compute local interest for both            # building types: the parcel's type and the seeded type            cur_interest = max(0., self[cur_type].get_interest(seed, other_parcels))            new_interest = max(0., self[new_type].get_interest(seed, other_parcels))            if bernouilli(0.3*(new_interest - cur_interest) + 0.7*new_interest):                # todo: replace with max search ?                self.__change_parcel_type(parcel, new_type)                return cur_type        return new_type    def __change_parcel_type(self, parcel: Parcel, new_type: BuildingType):        """        Changes the type of a parcel and updates all the interest maps (sociability) accordingly        """        old_type = parcel.building_type  # stores replaced type        parcel.building_type = new_type  # change parcel type        for typed_interest_map in self.__interest_maps.values():            # updates pre computed sociability when necessary            typed_interest_map.notify_type_change(self.__parcels, parcel, old_type)        # Set the building type to be seeded        print("Replaced {} parcel at {} with type {}".format(old_type.name, parcel.center, parcel.building_type.name))    def get_optimal_type(self, seed):        # type: (Point) -> BuildingType        """        For a seed, returns a type with the highest interest        """        int_seed = Point(round(seed.x), round(seed.z))        building_type_iter = self.__interest_maps.items()        type_interest = {b_type: b_map.get_interest(int_seed, self.__parcels) for b_type, b_map in building_type_iter}        max_interest = max(type_interest.values())        if max_interest == -1:            return BuildingType.ghost        else:            best_types = list(filter(lambda b_type: type_interest[b_type] == max_interest, type_interest))            return choice(best_types)class InterestMap:    """    Stores precomputed interest matrices for a given building type and contains methods to quickly update these matrices    """    def __init__(self, building_type: BuildingType, scenario: str, terrain_maps: TerrainMaps, districts: Districts):        # Parameters        self.__type = building_type  # type: BuildingType        self.__road_net = terrain_maps.road_network  # type: RoadNetwork        self.__districts = districts        self.__known_seeds = 0  # type: int        self.__scenario = scenario        self.__size = terrain_maps.width, terrain_maps.length        # Weights        scenario_dict = BUILDING_ENCYCLOPEDIA[scenario]        self.__lambdas = {criteria: scenario_dict[criteria][building_type.name]                          for criteria in scenario_dict if building_type.name in scenario_dict[criteria]}        self.__lambdas["Sociability"] = scenario_dict["Sociability"]        self.__acc_w = self.__lambdas["Weighting_factors"][0]        self.__soc_w = self.__lambdas["Weighting_factors"][1]        self.__fix_w = sum(self.__lambdas["Weighting_factors"][3:])        # Interest functions        self.__access = None        self.__social = None        self.__fixed_interest = self.__compute_fixed_interest(terrain_maps)        self.__interest_value = None    def update(self, __parcels):        """        Updates the interest matrix with the newest road network and parcels added since last update        """        n, m = self.__known_seeds, len(__parcels) - self.__known_seeds        if n == 0:            # currently, density is a fixed interest but requires existing parcels (town center)            # so it is added now to the fixed interest, at the first call of this method            dense_intrst = density(self.__size, self.__districts, self.__lambdas["Density"])            dense_weight = self.__lambdas["Weighting_factors"][2]            fixed_intrst = self.__fixed_interest            fixed_weight = self.__fix_w            self.__fix_w += dense_weight            self.__fixed_interest = ((fixed_intrst * fixed_weight) + (dense_intrst * dense_weight)) / self.__fix_w            self.__fixed_interest[(fixed_intrst == -1) | (dense_intrst == -1)] = -1        if m > 0:            self.__access = accessibility(self.type, self.scenario, self.__road_net, self.__size)            old_soc = self.__social            new_soc = sociability(self.type, self.scenario, __parcels[n:], self.__size)            if old_soc is None:                self.__social = new_soc            else:                self.__social = (old_soc * n + new_soc * m) / (n + m)                self.__social[(old_soc == -1) | (new_soc == -1)] = -1            self.__known_seeds += m            self.__compute_interest()    def get_seed(self, max_iteration=None, perc=95):        assert self.__interest_value is not None        length = self.__interest_value.shape[1]        size = self.__interest_value.size        cells_ids: List[int] = list(range(size))        reachable_high_interest = percentile(self.__interest_value, perc)        cells_ids = list(filter(lambda pos: (self.__interest_value[pos // length, pos % length] >= reachable_high_interest), cells_ids))        if not cells_ids:            return None  # all positions have a negative interest: impossible to seed        random.shuffle(cells_ids)  # shuffles in place        if max_iteration and max_iteration < len(list(cells_ids)):            cells_ids = cells_ids[:max_iteration]  # limit search to first max_iter elements        for random_index in cells_ids:            x, z = random_index // length, random_index % length  # convert index to coordinates            interest_score = self.__interest_value[x, z]            if bernouilli(interest_score):                return Point(x, z)        return None    def __compute_fixed_interest(self, maps: TerrainMaps):        """        Computes interest for fixed functions (relative to the terrain).        Should be called only once -- at the instance init        """        _t = time.time()        def river_interest(_x, _z):            if maps.fluid_map.has_river:                return close_distance(maps.fluid_map.river_distance[_x, _z], self.__lambdas["RiverDistance"])            return 0        def ocean_interest(_x, _z):            if maps.fluid_map.has_ocean:                return close_distance(maps.fluid_map.ocean_distance[_x, _z], self.__lambdas["OceanDistance"])            return 0        def lava_interest(_x, _z):            if maps.fluid_map.has_lava:                return obstacle(maps.fluid_map.lava_distance[_x, _z], self.__lambdas["LavaObstacle"])            return 0        def altitude_interest(_x, _z):            alt = maps.height_map[_x, _z]            lm, l0, lM = self.__lambdas["Altitude"]            return balance(alt, lm, l0, lM)        def steepness_interest(_x, _z):            steep = maps.height_map.steepness(_x, _z)            return open_distance(steep, self.__lambdas["Steepness"])        size = maps.width, maps.length        _interest_map = np.zeros(size)        extendability_map = extendability(size, MIN_PARCEL_SIZE)        altitude_interest_map = np.array([[altitude_interest(x, z) for z in range(size[1])] for x in range(size[0])])        steep_interest_map = np.array([[steepness_interest(x, z) for z in range(size[1])] for x in range(size[0])])        ocean_interest_map = np.array([[ocean_interest(x, z) for z in range(size[1])] for x in range(size[0])])        river_interest_map = np.array([[river_interest(x, z) for z in range(size[1])] for x in range(size[0])])        lava_interest_map = np.array([[lava_interest(x, z) for z in range(size[1])] for x in range(size[0])])        for x, z, in itertools.product(range(size[0]), range(size[1])):            interest_functions = np.array([                altitude_interest_map[x, z],                river_interest_map[x, z],                ocean_interest_map[x, z],                lava_interest_map[x, z],                steep_interest_map[x, z]            ])            if min(interest_functions) == -1 or extendability_map[x][z] == -1:                interest_score = -1            else:                weights = np.array(self.__lambdas["Weighting_factors"][3:])                interest_score = interest_functions.dot(weights) / sum(weights)                # interest_score = max(-1, weighted_score)            _interest_map[x][z] = interest_score        print("[InterestMap] Computed fixed interest functions for type {} in {:0.2} s".format(self.type.name, time.time() - _t))        return _interest_map    def __compute_interest(self):        """        Must be called when any of the interest matrices are modified to update the main interest matrix        """        a, s, f = self.__acc_w, self.__soc_w, self.__fix_w        mask = (self.__access == -1) | (self.__social == -1) | (self.__fixed_interest == -1)        soc: ndarray = self.__social        min_soc = soc.min()        max_soc = soc.max()        soc = 2 * (soc - min_soc) / (max_soc - min_soc) - 1        self.__interest_value = (self.__access * a + soc * s + self.__fixed_interest * f) / (a + s + f)        self.__interest_value[mask] = -1    def get_interest(self, seed, parcels=None):        # type: (Point, List[Parcel]) -> float        """        Returns interest value at a given seed. If a list of parcels is passed, will recompute local accessibility        and sociability from this parcel list        """        if parcels is None:            return self.__interest_value[seed.x, seed.z]        local_acc = local_accessibility(seed.x, seed.z, self.type, self.scenario, self.__road_net)        local_soc = local_sociability(seed.x, seed.z, self.type, self.scenario, parcels)        local_fix = self.__fixed_interest[seed.x, seed.z]        if local_acc == -1 or local_soc == -1 or local_fix == -1:            return -1        a, s, f = self.__acc_w, self.__soc_w, self.__fix_w        return (local_acc * a + local_soc * s + local_fix * f) / (a + s + f)    def notify_type_change(self, parcels, parcel, old_type):        """        When an existing parcel changes type, recomputing in sociability (and interest) matrices may be necessary        """        if parcel not in parcels[:self.__known_seeds]:            # parcel with old type has no effect on self.__access -> nothing to do            return        # Update sociability matrix        old_lambda = self.__lambdas["Sociability"]["-".join([self.type.name, old_type.name])]        old_social = sociability_one_seed(*old_lambda, parcel.mean_x, parcel.mean_z, self.__size)        new_lambda = self.__lambdas["Sociability"]["-".join([self.type.name, parcel.building_type.name])]        new_social = sociability_one_seed(*new_lambda, parcel.mean_x, parcel.mean_z, self.__size)        self.__social += (new_social - old_social) / self.__known_seeds        self.__social[new_social == -1] = -1        for x, z in filter(lambda xz: old_social[xz] == -1, itertools.product(range(self.__size[0]), range(self.__size[1]))):            self.__social[x, z] = local_sociability(x, z, self.type, self.scenario, parcels[:self.__known_seeds])        # Compute interest with the updated sociability matrix        self.__compute_interest()    @property    def type(self):        return BuildingType(self.__type)    @property    def scenario(self):        return str(self.__scenario)    @property    def accessibility(self):        return array(self.__access)    @property    def sociability(self):        return array(self.__social)    @property    def map(self):        return array(self.__interest_value)