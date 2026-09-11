# Шпаргалка по Python & C++

Универсальная шпаргалка для маленьких экранов **320×240** (умные часы, микроконтроллеры ESP32, портативные читалки).

## 1. Срезы списков (Slices)
В Python синтаксис срезов: `list[start:stop:step]`.

- `lst[::-1]` — развернуть список задом наперёд
- `lst[:5]` — первые 5 элементов
- `lst[-3:]` — последние 3 элемента

```python
data = [10, 20, 30, 40, 50]
print("Reversed:", data[::-1])
```

> **Совет**: срезы создают неглубокую копию списка (shallow copy).

---page---

## 2. Алгоритмы поиска

### Быстрый бинарный поиск
Работает только на **отсортированном** массиве со сложностью *O(log N)*.

```cpp
int binary_search(int arr[], int n, int target) {
    int left = 0, right = n - 1;
    while (left <= right) {
        int mid = left + (right - left) / 2;
        if (arr[mid] == target) return mid;
        if (arr[mid] < target) left = mid + 1;
        else right = mid - 1;
    }
    return -1;
}
```

---page---

## 3. Микроконтроллер ESP32

Полезные пины и периферия:
1. `GPIO 21 / 22` — стандартная шина I2C (SDA / SCL)
2. `GPIO 18 / 23` — шина SPI (SCK / MOSI)
3. `ADC1 (GPIO 32-39)` — аналоговые входы, работающие вместе с Wi-Fi

> **Внимание**: `ADC2` отключается при активном радиомодуле Wi-Fi!

```python
from machine import Pin, ADC
sensor = ADC(Pin(34))
sensor.atten(ADC.ATTN_11DB)
val = sensor.read()
```
