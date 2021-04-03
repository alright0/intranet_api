# intranet_api

Это приложение является внутренним сайтом,на котором находится два основных раздела: Сайт с дэшбордами и API, которое позволяет другим приложениям иметь доступ к базе. К сожалению, я не могу предоставить полную информацию, поэтому на некоторых скриншотах заблюрена или стерта некоторая информация.

**Сайт**

На данный момент сайт содержит в себе несколько разделов:

**1. index:**
Здесь находится информация о состоянии линий на текущий момент: стоит линия или работает, кто находится на линии, какой выпуск, процент брака(там где есть камеры), номер заказа и его описание. Возможность собирать информацию по проценту брака появилась благодаря <a href="https://github.com/alright0/ibea_to_pg">скрипту</a>, который асинхронно опрашивает камеры и пишет значения в базу. Осталньные показатели берутся из соседней основной базы.
На данном этапе автообновление организовано с помощью обновления всего html, но в дальнейшем я планирую перевести его на ajax-запросы.
<p align="center"><img width=700px src="https://user-images.githubusercontent.com/71926912/113477223-0f1e3380-9489-11eb-88cc-772822862dd9.jpg"></p>

**2. month_report:**
Здесь находится информация о состоянии производства за месяц. Графики выпуска, эффективные и неэффективные смен, динамика работы линий и т.п. 
<p align="center"><img width=700px src="https://user-images.githubusercontent.com/71926912/113477458-74beef80-948a-11eb-9e24-25986d6e0323.jpg"></p>

Поскольку основная <a href="https://github.com/alright0/intranet_api/blob/master/Statistics/logic/dataframes.py">логика</a> написана в ООП стиле, это позволяет получать и обрабатывать данные довольно гибко за желаемый период времени(необходимо указать параметры при создании экземпляра класса up_puco_table. подробности в docstring к классу по <a href="https://github.com/alright0/intranet_api/blob/master/Statistics/logic/dataframes.py">ссылке</a>). Все таблицы и графики являются экземплярами класса, поэтому их можно просто вызвать и получить готовый набор данных, который необходимо будет встроить в html. При создании этой страницы очень помог опыт, полученный при создании <a href="https://github.com/alright0/Dashboard">приложений на dash</a>.


В планах добавление пользователей с разными уровнями доступа к информации

<b>API</b>

На данный момент api существует два вида оветов api:
1. **../camera/last/\<line\>** - Это место возвращает последнюю запись в базе по данной камере(по полю "line_side") и возвращает ответ вида:
```
{
  "date_now": "Thu, 18 Mar 2021 09:17:05 GMT", 
  "id": 7, 
  "job": "10163", 
  "last_part": "Thu, 18 Mar 2021 09:16:33 GMT", 
  "line": "LZ-1", 
  "line_side": "LZ-1 A", 
  "message": "OK", 
  "rejected": 58, 
  "start_time": "Thu, 18 Mar 2021 08:00:03 GMT", 
  "total": 9796
}
``` 
  
  или 
  
```
{
  "message": "data not found"
}
```
2. **../camera/\<line\>** - возвращает то же, что и первый ответ, только по полю "line", которое может иметь более одного значения "line_side" 

Дальнейшее развитие этого **API** состоит в том, чтобы ставить на линии дешевые датчики на базе **Arduino** и **ESP8266** для отслеживания некоторых некритически важных параметров линий и производства в целом: уровень воды в водонапорной башне, наличие поддонов в нужных местах и т.п. - запись информации с датчиков в базу можно организовать через **POST** запросы к этому **API** и дальнейшее чтение через это же **API**. Также в дальнейшем планирую подключить **swagger**, думаю, это сэкономит кучу времени в будущем.





<!-- <p align="center"><img width=700px src=""></p> -->
