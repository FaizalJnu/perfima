import pytest
from datetime import date, datetime
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from perfima.services import report_service
from unittest.mock import MagicMock

@pytest.fixture
def mock_plt(mocker):
    return mocker.patch('perfima.services.report_service.plt')

@pytest.fixture
def mock_db():
    return Mock(spec=Session)

@pytest.fixture
def mock_io(mocker):
    return mocker.patch('perfima.services.report_service.io')

@pytest.fixture
def mock_base64(mocker):
    return mocker.patch('perfima.services.report_service.base64')

@pytest.fixture
def mock_io():
    with patch('perfima.services.report_service.io') as mock:
        yield mock

@pytest.fixture
def mock_base64():
    with patch('perfima.services.report_service.base64') as mock:
        yield mock
        
class FlexibleMock(Mock):
    def __iter__(self):
        return iter([])
    
    def __getitem__(self, item):
        return self

@pytest.fixture
def mock_db():
    mock = Mock(spec=Session)
    mock.query.return_value = FlexibleMock()
    return mock

def test_get_last_year_date_range():
    with patch('perfima.services.report_service.datetime') as mock_datetime:
        mock_datetime.utcnow.return_value = datetime(2023, 6, 1)
        start_date, end_date = report_service.get_last_year_date_range()
        assert start_date == date(2022, 6, 1)
        assert end_date == date(2023, 6, 1)


def test_get_monthly_report(mock_db):
    mock_db.query.return_value.filter.return_value.scalar.side_effect = [1000, 500, 200]
    mock_db.query.return_value.filter.return_value.distinct.return_value = []

    result = report_service.get_monthly_report(mock_db, user_id=1, year=2023, month=6)
    assert result == {
        "income": 1000,
        "expenses": 500,
        "savings": 200,
        "net": 500,
        "start_date": date(2023, 6, 1),
        "end_date": date(2023, 6, 30)
    }

def test_get_yearly_report(mock_db):
    with patch('perfima.services.report_service.get_last_year_date_range') as mock_date_range:
        mock_date_range.return_value = (date(2022, 6, 1), date(2023, 6, 1))
        mock_db.query.return_value.filter.return_value.scalar.side_effect = [12000, 6000, 2400]
        mock_db.query.return_value.filter.return_value.distinct.return_value = []

        result = report_service.get_yearly_report(mock_db, user_id=1)
        assert result == {
            "income": 12000,
            "expenses": 6000,
            "savings": 2400,
            "net": 6000,
            "start_date": date(2022, 6, 1),
            "end_date": date(2023, 6, 1)
        }

def test_get_monthly_category_report(mock_db, mock_plt, mock_io, mock_base64):
    mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
        ("Category1", 1000, 500),
        ("Category2", 500, 200)
    ]
    mock_db.query.return_value.filter.return_value.distinct.return_value = [("Category1",)]
    mock_io.BytesIO.return_value.getvalue.return_value = b'mock_image'
    mock_base64.b64encode.return_value.decode.return_value = 'base64_encoded_image'

    result = report_service.get_monthly_category_report(mock_db, user_id=1, year=2023, month=6)

    assert result['category_report'] == {
        "Category1": {"income": 1000, "expenses": 500},
        "Category2": {"income": 500, "expenses": 200}
    }
    assert result['total_income'] == 1500
    assert result['total_expense'] == 700
    assert result['total_savings'] == 1000
    assert result['net'] == 800
    assert result['start_date'] == date(2023, 6, 1)
    assert result['end_date'] == date(2023, 6, 30)
    assert 'income_chart' in result
    assert 'expense_chart' in result
    assert 'summary_chart' in result

def test_get_yearly_category_report(mock_db, mock_plt, mock_io, mock_base64):
    with patch('perfima.services.report_service.get_last_year_date_range') as mock_date_range:
        mock_date_range.return_value = (date(2022, 6, 1), date(2023, 6, 1))
        mock_db.query.return_value.join.return_value.filter.return_value.group_by.return_value.all.return_value = [
            ("Category1", 12000, 6000),
            ("Category2", 6000, 2400)
        ]
        mock_db.query.return_value.filter.return_value.distinct.return_value = [("Category1",)]
        mock_io.BytesIO.return_value.getvalue.return_value = b'mock_image'
        mock_base64.b64encode.return_value.decode.return_value = 'base64_encoded_image'

        result = report_service.get_yearly_category_report(mock_db, user_id=1)

        assert result['category_report'] == {
            "Category1": {"income": 12000, "expenses": 6000},
            "Category2": {"income": 6000, "expenses": 2400}
        }
        assert result['total_income'] == 18000
        assert result['total_expense'] == 8400
        assert result['total_savings'] == 12000
        assert result['net'] == 9600
        assert result['start_date'] == date(2022, 6, 1)
        assert result['end_date'] == date(2023, 6, 1)
        assert 'income_chart' in result
        assert 'expense_chart' in result
        assert 'summary_chart' in result
        
def test_get_saving_categories(mock_db):
    mock_category1 = Mock()
    mock_category1.name = "Savings"
    mock_category2 = Mock()
    mock_category2.name = "Investments"
    mock_db.query.return_value.join.return_value.filter.return_value.all.return_value = [
        mock_category1,
        mock_category2
    ]
    result = report_service.get_saving_categories(mock_db, user_id=1)
    assert result == ["Savings", "Investments"]

def test_genPi(mock_plt, mock_io, mock_base64):
    labels = ["Category1", "Category2"]
    sizes = [60, 40]
    title = "Test Chart"

    mock_io.BytesIO.return_value.getvalue.return_value = b'mock_image'
    mock_base64.b64encode.return_value.decode.return_value = 'base64_encoded_image'

    result = report_service.genPi(labels, sizes, title)

    assert result == 'base64_encoded_image'
    mock_plt.figure.assert_called_once_with(figsize=(10, 10))
    mock_plt.pie.assert_called_once_with(sizes, labels=labels, autopct='%1.1f%%', startangle=90)
    mock_plt.axis.assert_called_once_with('equal')
    mock_plt.title.assert_called_once_with(title)
    mock_plt.savefig.assert_called_once()
    mock_plt.close.assert_called_once()