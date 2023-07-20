## Kawiarnia

_Weronika Łoboz, Kamil Obeidat, Zofia Burchard_

Projekt studencki - prosty program dla pracowników kawiarni z grami planszowymi.
Można: rezerwować stoliki i gry na konkretne daty/godziny, a także zamawiać jedzenie.

Wybrane technologie: Python + MongoDB

### Jak uruchomić

Zakładając, że został uruchomiony serwer MongoDB na localhoście na standardowym porcie:

```console
$ pip install -r requirements.txt
$ uvicorn main:app --reload
```
W folderze test_database są wygenerowane kolekcje testowe które można przez Compass/shella/itp zaimportować do MongoDB jako 'test_database'.

Automatycznie wygenerowaną dokumentację z możliwością wykonania poleceń można znaleźć pod adresem <http://localhost:8000/docs>

Id w bazie są prostymi intami, nadawanymi sekwencyjnie - jest to baza dla pracowników niewielkiej kawiarni, więc nie przewidujemy równoczesnego dostępu z wielu terminali. Może być przechowywana lokalnie lub na zdalnym serwerze - korzystamy z protokołu http żeby to umożliwić.

Daty/czas są przechowywane jako datetime - format obsługiwany zarówno przez Pythona jak i przez MongoDB. Jest on dosyć uciążliwy do 'ręcznego' wpisywania do bazy, ale wychodzimy z założenia że jego wyświetlanie/wprowadzenie do bazy odbywałoby się od strony frontendu.

### Model
Baza składa się z 4 kolekcji które zostały zaprojektowane w taki sposób, żeby nie musieć robić lookupów pomiędzy nimi.

**Games** - przechowuje listę gier które klienci mogą wypożyczyć. Każda gra ma nazwę (name - str), informacje o liczbie graczy dla których jest przeznaczona (minPlayers, maxPlayers - int), tagi (np. 'strategy' - str) po których można wyszukać interesujące klienta gry, ilość sztuk na stanie (unitsInStock - int) i listę rezerwacji (reservations - lista obiektów dict o polach 'reservation_id', 'endTime', 'startTime').
Przykładowy obiekt gra w bazie:

![image](https://github.com/wloboz/BD2/assets/94412369/e5551d69-c039-4e5b-a5a2-8a49f6f026ba)

**Menu** - lista oferowanych napojów i posiłków. Każda pozycja ma nazwę (name - str), dostępność (available - bool - do użytku gdy coś wychodzi z menu na dłuższy czas), cenę (float) i tagi (np. 'słone').
Przykładowy obiekt menu w bazie:
![image](https://github.com/wloboz/BD2/assets/94412369/d06edf46-b95a-4db0-98c6-a05b59b3045b)


**Tables** - lista stolików w kawiarni. Każdy stolików ma ilość dostępnych miejsc oraz listę rezerwacji dla tego stolika.
Przykładowy obiekt stolik w bazie:

![image](https://github.com/wloboz/BD2/assets/94412369/77c80ae8-1f93-44a8-a71d-8382bcba7460)


**Reservations** - przechowuje listę rezerwacji. Ma czasy od-do (startTime, endTime - datetime), imię/nazwisko klienta na które była stworzona rezerwacja, tablicę zarezerwowanych gier (podane id i nazwa gry), tablicę zamówionego jedzenia (obiekty słownikowe o polach name, quantity, price - cena jest automatycznie wyszukiwana w bazie w momencie złożenia zamówienia, ale jeżeli potem się zmieni to w rezerwacji zostanie ta stara), ilość klientów i tablicę stolików jakie są dla nich zarezerwowane.
Przykładowy obiekt rezerwacji w bazie:
![image](https://github.com/wloboz/BD2/assets/94412369/611b0a4e-f7a9-40cc-a782-d33416a1f6bc)



### Funkcje
Wszystkie kolekcje obsługują standardowe zapytania:
 - get - wiele na raz, z ustawionymi przez użytkownika dodatkowymi kryteriami lub 1 po id
 - put - jeden dokument na raz, gry i menu obsługują dodawanie wielu pozycji na raz
 - patch - jeden na raz po id, wiele na raz według podanych kryteriów w grach i w menu
 - delete - jeden na raz, po id



**Menu**
- get_menu:wyszukiwanie obiektów z menu za pomocą kilku parametrów: CENA- lt oznacza less then, lte - less then or equal, gt, gte - analogicznie,DOSTĘPNOŚĆ- wyszukiwanie dostępchych/niedostępnych pozycji z menu,  Tags: podać po przecinku, np. 'napoje, słodkie'. Listę wszystkich tagów można zobaczyć pod adresem http://localhost:8000/tags/menu lub za pomocą funkcji get_menu_tags. Tagi są sprawdzane z warunkiem logicznym AND - rezultat pokaże wszystkie dokumenty mające wszystkie podane tagi. Tagi są case sensitive.
Z domyślnymi (pustymi) argumentami wyświetli wszystkie pozycje menu. Wyniki wyszukiwań można sortować po cenie za pomocą opcji sort_by_price.
![image](https://github.com/wloboz/BD2/assets/94412369/79d60129-76d4-441e-b3cd-bc1ad30a778a)

- put_menu_item: należy podać nowy dokument w formacie:
```
{"name": "Herbata mrożona", "price": 11.99, "tags": ["napoje", "słodkie"]}
```
- put_multiple_menu_items: formatowanie jak wyżej, należy podać listę takich obiektów. Jest sprawdzane czy coś nie jest "zdublowane" po nazwie (ale uwaga: sprawdzanie jest case sensitive, więc Kawa Czarna != Kawa czarna) i wtedy taki obiekt nie jest dodawany (pozostałe są). Walidacja, aby cena obiektu nie była poniżej 0
- patch_menu_item-aktualizacja obiektu z pozycji z menu po id, np, gdy checemy zmienić aktualną cenę pozycji.
- patch_menu_items- aktualizacja kilku pozycji
- delete_menu_items- usuwanie pozycji z menu po id

**Games**
- get_games: wyszukiwanie po parametrach takich jak liczby graczy: wszystkie wartości do wyszukiwania są ustawione na 'greater/lesser than or equal', nazwa oraz przez tagi. Lista tagów dostępna pod adresem http://localhost:8000/tags/games lub funkcją get_games_tags. Tagi są sprawdzane z warunkiem logicznym AND - rezultat pokaże wszystkie dokumenty mające wszystkie podane tagi. Tagi są case sensitive.
  ![image](https://github.com/wloboz/BD2/assets/94412369/48c19bbe-9294-4660-b521-b9afbec5352d)

- put_game_item: format:
```
{
    "name": "Pandemic",
    "minPlayers": 2,
    "maxPlayers": 4,
    "unitsInStock": 1,
    "tags": ["cooperative", "epidemic", "strategy"],
    "reservations": [{}]
}
```
- put_multiple_game_items: jak wyżej, tylko jako lista []
- add_reservation_to_game- gdy ktoś dodaje do rezerwacji grę, to id tej rezerwacji, czas rozpoczęcia oraz zakończenia rezerwacji także dodajemy do gry (uzupełniamy listę reservations o nową pozycję) w celu pózniej łatwiejszeo sprawdzania dostępności, gdy w danym przedziale czasu ilość rezerwacji będzie większa niż ilość dostępnych sztuk wybranej gry, wyskoczy error i uniemożliwi dodanie takiej rezerwacji z zajętą grą. Jeśli wszystko przebiegnie pomyślnie  gra (z dodaną rezerwacją ) zostanie zaktualizowana w bazie.

**Reservations**
- get_reservations: startNow (default: False) powoduje wyświetlenie listy nadchodzących/trwających rezerwacji posortowanych według czasu rozpoczęcia. Jeżeli jest True to opcje wyszukiwania po czasie są ignorowane, ale pozostałe działają. Pole gameList służy do szukania klientów którzy zamówili jakieś konkretne gry. Należy podać listę gier po przecinku, case sensitive. W przeciwieństwie do tagów obowiązuje tu warunek logiczny LUB - w wynikach będą rezerwacje które mają zamówioną przynajmniej jedną grę z podanych. Można także wyszukiwać rezerwacji w konkretnym przedziale czasowym oraz wszystkie rezerwację, które zostały dodane na wybraną osobę.
   ![image](https://github.com/wloboz/BD2/assets/94412369/f21d452d-ae0d-4286-9807-94db8a0aef3b)

- get_reservation_item: zwróci rezerwację po id i podliczony koszt zamówionego jedzenia.
- patch_reservation_item-aktualizacja rezerwacji
- put_reservation: przykładowy wpis:
```
{
  "_input": {
    "startTime": "2023-06-19T14:02:15.212Z",
    "endTime": "2023-06-19T14:02:20.212Z",
    "games": [
      {"id": 8, "name" : "Carcassonne"}
    ],
    "orderedFood": [
      {}
    ],
    "clients": 2,
    "clientName": "TestClient1",
    "tables": [
      0
    ]
  },
  "_food": [
    {
      "name": "Espresso",
      "quantity": 5,
      "price": 0
    }
  ]
}
```
Sprawdzamy czy wszystkie gry z rezerwacji są dostępne wywołując funkcję check_game_availability dla każdej z gry występującej w liście, jeśli którakolwiek z gier będzie niedostępna w tym terminie rezerwacja nie zostanie dodana do bazy. Sprawdzamy również czy stoliki dla podanej ilośći osób bedą dostępne w tym terminie wywołując funkcje check_chairs_avaiability, zwracającą tablicę z indeksami stolików do rezerwacji. Jeśli wszystko wykona się prawidłowo(dostępność gier i stolików jest poprawna) to dodajemy zapis o rezerwacji.
do wszystkich stolików oraz gier wywołujemy funkcje add_reservation_to_game oraz add_reservation_to_table, zapisującą w grze informacje o nowo dodanej rezerrwacji.
orderedFood w _input należy zostawić puste i podać listę zamówionego jedzenia w _food. Price należy zostawić jako 0 - zostanie ona automatycznie ustawiona na obowiązującą w menu cenę za sztukę.Sprawdzamy również czy każde z dodanego jedzenia jest dostępne.
- add_reservation_food: służy do dodawania jedzenia do istniejącej rezerwacji żeby klienci mogli domawiać jedzenie w trakcie pobytu w kawiarni.
- check_game_availability-sprawdzamy czy gra o podanym id oraz dacie rozpoczęcia i zakończenia rezerwacji jest dostępna
- check_chairs_availaility-sprawdzamy czy stoliki są dostępne oraz dodajemy wolne do listy, funkcja zwraca liste wolnych stolików dla podanej liczby gości.
- calculate_total_price -funkcja która oblicza cene całego zamówienia.
- delete_reservation_item - funkcja usuwa obiekt rezerwacji po id



 **Tables**
 
- get_tables- funkcja zwracająca wszystkie stoliki z bazy
![image](https://github.com/wloboz/BD2/assets/94412369/809fdad1-77df-426e-a362-8aedef55670a)
- get_table_item- funkcja zwracająca stolik po id
- put_table_item- funkcja dodająca nowy stolik do bazy, należy dodać jedynie ilość miejsc nowego stolika. Dany stolik będzie miał początkowo pustą tablicę rezerwacji.
- delete_table_item- usuwanie stolika po id
- add_reservation_to_table - dla podanego id rezerwacji oraz czasu rozpoczęcia i zakończenia dodajmy te infomacje do stolika, aby pózniej móc łatwiej szukać wolnych stolików dla kolejnych rezerwacji.

 **Inne**
 Są dwie wspomniane już funkcje pomocnicze do wyświetlania istniejących tagów:
 - get_games_tags i get_menu_tags

### Przewodnik po kodzie

`main.py` w korzeniu projektu służy jako punkt startowy dla serwera. W nim zdefiniowane jest główne API zgodnie z konwencjami FastAPI i podpięte są routery.

Routery zdefiniowane są w katalogu `routers` w module `cafe_api` <sup>[1](#apropos-modulu)</sup>. Każdy router z wyjątkiem `tags` jest podobnie napisany:

Najpierw opisane są 3 klasy: pierwsza `XyzInput` przeznaczona na dane wejściowe podawane przy tworzeniu zasoby, druga `Xyz` przeznaczona na reprezentację samego zasobu (dane wyjściowe) oraz trzecia `XyzPatch` przeznaczona na dane wejściowe podawane przy aktualizacji zasobu (wszystkie pola są opcjonalne). Generalnie te klasy są definiowane w tej kolejności: pierwsza dziedziczy po wspólnej klasie `Model` (o której więcej potem) i opisuje wypełnialne pola, druga dziedziczy po pierwszej i dodaje pola tylko do odczytu (jak identyfikator), a trzecia jest taka sama jak pierwsza, tylko że wszystkie pola są ustawione na opcjonalne (jest ona automatycznie generowana przez bibliotekę `pydantic-partial`).

Potem opisane są typowe routy:
 - `GET /xyz/:id` - zwraca obiekt (w formie `Xyz`) pod odpowiednim `id`
 - `GET /xyz/` - zwraca listę obiektów z ewentualnymi filtrami (zależne od poszczególnego modelu)
 - `PUT /xyz/` - wstawia nowy obiekt na podstawie podanego `XyzInput` i ją zwraca
 - `PATCH /xyz/:id` - aktualizuje obiekt pod odpowiednim `id` na podstawie podanego `XyzPatch` i ją zwraca

Poza powyższymi routami mogą zostać opisane dodatkowe w zależności od potrzeb modelu.

Wspólna klasa `Model` służy uniknięciu zbędnej duplikacji kodu. Opisane są w niej typowe operacje i zapytania bazodanowe, z których korzystają wszystkie modele. Te operacje są zaimplementowane przez metody klasowe, które działają podobnie do metod statycznych, tylko że pozwalają na introspekcję klasową. Ta introspekcja jest używana przede wszystkim po to, aby pobrać informację o nazwie używanej kolekcji. W metodzie `get_collection` znajduje się nieco kryptyczny kod, który konwertuje nazwę klasy w camel casie na nazwę kolekcji w snake casie, a następnie zwraca tąże kolekcję. Różne metody zostały napisane dla działania na wielu i jednym dokumencie w celach wydajnościowych.

---
<a name="apropos-modulu">1</a>: Moduł `cafe_api` zawiera cały kod oprócz pliku `main.py`. Plik główny został "wyciągnięty" z modułu w celu zachowania kompatybilności z różnymi wersjami Pythona, tak żeby każdemu z nas działał.
