import datetime

from django.contrib.auth import get_user_model
from django.db.models import Count, Q
from django.db.models.functions import Coalesce, TruncDay, TruncWeek
from django.shortcuts import get_object_or_404
from django.utils.dateparse import parse_date
from rest_framework.decorators import api_view, permission_classes
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response

from accounts.permissions import IsManagerOrAdmin
from tasks.models import Tache, SousTache, Semaine
from reports.models import RapportExecution

User = get_user_model()


MOIS_ABBR = {
    1: 'janv.', 2: 'févr.', 3: 'mars', 4: 'avr.', 5: 'mai', 6: 'juin',
    7: 'juil.', 8: 'août', 9: 'sept.', 10: 'oct.', 11: 'nov.', 12: 'déc.',
}


# --------------------------------------------------------------------------
# Helpers communs
# --------------------------------------------------------------------------

def _parse_periode(request):
    """
    Lit ?date_debut=YYYY-MM-DD&date_fin=YYYY-MM-DD.
    Retourne (date_debut, date_fin) comme objets `date` Python, ou
    (None, None) si aucun des deux n'est fourni (comportement historique :
    pas de filtre = tout l'historique).
    """
    brut_debut = request.query_params.get('date_debut')
    brut_fin = request.query_params.get('date_fin')

    if not brut_debut and not brut_fin:
        return None, None

    date_debut = parse_date(brut_debut) if brut_debut else None
    date_fin = parse_date(brut_fin) if brut_fin else None

    if brut_debut and date_debut is None:
        raise ValidationError({'date_debut': "Format attendu : YYYY-MM-DD."})
    if brut_fin and date_fin is None:
        raise ValidationError({'date_fin': "Format attendu : YYYY-MM-DD."})
    if date_debut and date_fin and date_debut > date_fin:
        raise ValidationError("date_debut doit être antérieure ou égale à date_fin.")

    return date_debut, date_fin


def _exiger_periode(request):
    """Comme _parse_periode, mais lève une erreur si la période est absente
    (utilisé pour /evolution/, où une fenêtre bornée est indispensable)."""
    date_debut, date_fin = _parse_periode(request)
    if not date_debut or not date_fin:
        raise ValidationError(
            "date_debut et date_fin (YYYY-MM-DD) sont obligatoires pour cet endpoint."
        )
    return date_debut, date_fin


def _appliquer_periode(queryset, date_debut, date_fin, champ='date_creation'):
    """Filtre un queryset sur [date_debut, date_fin] inclus, bornes en jours complets."""
    if date_debut:
        queryset = queryset.filter(**{f'{champ}__date__gte': date_debut})
    if date_fin:
        queryset = queryset.filter(**{f'{champ}__date__lte': date_fin})
    return queryset


def _bloc_periode(date_debut, date_fin):
    """Construit le bloc 'periode' de la réponse, ou None si pas de filtre."""
    if not date_debut and not date_fin:
        return None
    return {
        'date_debut': date_debut.isoformat() if date_debut else None,
        'date_fin': date_fin.isoformat() if date_fin else None,
    }


def _pct(numerateur, denominateur):
    if not denominateur:
        return 0.0
    return round(numerateur / denominateur * 100, 1)


def _compter_par_status(queryset):
    return queryset.aggregate(
        total=Count('id'),
        terminees=Count('id', filter=Q(status='completed')),
        non_executees=Count('id', filter=Q(status='not_done')),
        en_cours=Count('id', filter=Q(status='in_progress')),
        en_attente=Count('id', filter=Q(status='pending')),
    )


def _label_jour(jour):
    return f"{jour.day:02d} {MOIS_ABBR[jour.month]}"


def _label_semaine(debut, fin):
    if debut.month == fin.month:
        return f"{debut.day:02d}–{fin.day:02d} {MOIS_ABBR[fin.month]}"
    return f"{debut.day:02d} {MOIS_ABBR[debut.month]}–{fin.day:02d} {MOIS_ABBR[fin.month]}"


def _points_evolution(tache_qs, granularite, date_fin_globale):
    """Regroupe un queryset de Tache par semaine ou par jour."""
    trunc = TruncWeek if granularite == 'semaine' else TruncDay

    groupes = (
        tache_qs
        .annotate(periode=trunc('date_creation'))
        .values('periode')
        .annotate(
            total=Count('id'),
            terminees=Count('id', filter=Q(status='completed')),
            non_executees=Count('id', filter=Q(status='not_done')),
            en_cours=Count('id', filter=Q(status='in_progress')),
            en_attente=Count('id', filter=Q(status='pending')),
        )
        .order_by('periode')
    )

    points = []
    for g in groupes:
        debut_periode = g['periode'].date() if hasattr(g['periode'], 'date') else g['periode']

        if granularite == 'semaine':
            fin_periode = debut_periode + datetime.timedelta(days=6)
            if date_fin_globale and fin_periode > date_fin_globale:
                fin_periode = date_fin_globale
            label = _label_semaine(debut_periode, fin_periode)
        else:
            fin_periode = debut_periode
            label = _label_jour(debut_periode)

        points.append({
            'periode_label': label,
            'date_debut': debut_periode.isoformat(),
            'date_fin': fin_periode.isoformat(),
            'total': g['total'],
            'terminees': g['terminees'],
            'non_executees': g['non_executees'],
            'en_cours': g['en_cours'],
            'en_attente': g['en_attente'],
            'taux_execution': _pct(g['terminees'], g['total']),
        })

    return points


def _nom_agent(user):
    nom = f"{user.first_name} {user.last_name}".strip()
    return nom or user.username


# --------------------------------------------------------------------------
# 1. GET /stats/ (extension rétrocompatible)
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def statistiques_generales(request):
    """
    Statistiques globales. Sans date_debut/date_fin : tout l'historique
    (comportement identique à avant). Avec ces paramètres : filtre sur
    date_creation de la tâche.
    """
    date_debut, date_fin = _parse_periode(request)

    tache_qs = _appliquer_periode(Tache.objects.all(), date_debut, date_fin)

    sous_tache_qs = SousTache.objects.all()
    if date_debut or date_fin:
        sous_tache_qs = _appliquer_periode(
            sous_tache_qs, date_debut, date_fin, champ='tache__date_creation'
        )

    agg = _compter_par_status(tache_qs)
    total = agg['total']

    reponse = {
        'total_taches': total,
        'taches_terminees': agg['terminees'],
        'taches_non_executees': agg['non_executees'],
        'taches_en_cours': agg['en_cours'],
        'taches_en_attente': agg['en_attente'],
        'taux_execution': _pct(agg['terminees'], total),
        'taux_non_execution': _pct(agg['non_executees'], total),
        'total_sous_taches': sous_tache_qs.count(),
        'sous_taches_terminees': sous_tache_qs.filter(status='completed').count(),
    }

    periode = _bloc_periode(date_debut, date_fin)
    if periode:
        reponse['periode'] = periode

    return Response(reponse)


# --------------------------------------------------------------------------
# 2. GET /stats/evolution/ (nouveau)
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def stats_evolution(request):
    """Évolution des tâches regroupées par semaine ou par jour sur une fenêtre."""
    date_debut, date_fin = _exiger_periode(request)

    granularite = request.query_params.get('granularite', 'semaine')
    if granularite not in ('semaine', 'jour'):
        raise ValidationError("granularite doit être 'semaine' ou 'jour'.")

    tache_qs = _appliquer_periode(Tache.objects.all(), date_debut, date_fin)
    points = _points_evolution(tache_qs, granularite, date_fin)

    return Response({
        'granularite': granularite,
        'points': points,
    })


# --------------------------------------------------------------------------
# 3. GET /stats/agents/ (extension)
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def statistiques_par_agent(request):
    """Statistiques par agent, avec fenêtre de dates optionnelle."""
    date_debut, date_fin = _parse_periode(request)

    tache_qs = _appliquer_periode(Tache.objects.all(), date_debut, date_fin)

    stats = tache_qs.values(
        'assigne_a_id', 'assigne_a__username',
        'assigne_a__first_name', 'assigne_a__last_name'
    ).annotate(
        total_taches=Count('id'),
        taches_terminees=Count('id', filter=Q(status='completed')),
        taches_non_executees=Count('id', filter=Q(status='not_done')),
        taches_en_cours=Count('id', filter=Q(status='in_progress')),
        taches_en_attente=Count('id', filter=Q(status='pending')),
    ).order_by('-total_taches')

    agents = []
    for a in stats:
        nom = f"{a['assigne_a__first_name']} {a['assigne_a__last_name']}".strip()
        agents.append({
            'agent_id': a['assigne_a_id'],
            'agent_nom': nom or a['assigne_a__username'],
            'total_taches': a['total_taches'],
            'taches_terminees': a['taches_terminees'],
            'taches_non_executees': a['taches_non_executees'],
            'taches_en_cours': a['taches_en_cours'],
            'taches_en_attente': a['taches_en_attente'],
            'taux_execution': _pct(a['taches_terminees'], a['total_taches']),
        })

    reponse = {'agents': agents}
    periode = _bloc_periode(date_debut, date_fin)
    if periode:
        reponse['periode'] = periode

    return Response(reponse)


# --------------------------------------------------------------------------
# 4. GET /stats/agents/<id>/evolution/ (nouveau)
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def stats_agent_evolution(request, agent_id):
    """Évolution des tâches d'un agent précis (drill-down au clic)."""
    date_debut, date_fin = _exiger_periode(request)

    granularite = request.query_params.get('granularite', 'semaine')
    if granularite not in ('semaine', 'jour'):
        raise ValidationError("granularite doit être 'semaine' ou 'jour'.")

    agent = get_object_or_404(User, pk=agent_id)

    tache_qs = _appliquer_periode(
        Tache.objects.filter(assigne_a=agent), date_debut, date_fin
    )
    points = _points_evolution(tache_qs, granularite, date_fin)

    return Response({
        'agent_id': agent.id,
        'agent_nom': _nom_agent(agent),
        'granularite': granularite,
        'points': points,
    })


# --------------------------------------------------------------------------
# 5. GET /stats/raisons/ (extension)
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def raisons_non_execution(request):
    """Répartition des raisons de non-exécution, avec pourcentage calculé côté serveur."""
    date_debut, date_fin = _parse_periode(request)

    rapports = RapportExecution.objects.filter(
        type_rapport='non_execution'
    ).annotate(
        date_ref=Coalesce('tache__date_creation', 'sous_tache__tache__date_creation')
    )
    if date_debut:
        rapports = rapports.filter(date_ref__date__gte=date_debut)
    if date_fin:
        rapports = rapports.filter(date_ref__date__lte=date_fin)

    total = rapports.count()
    par_categorie = rapports.values('categorie_raison').annotate(
        count=Count('id')
    ).order_by('-count')

    libelles = dict(RapportExecution._meta.get_field('categorie_raison').choices)

    raisons = []
    for r in par_categorie:
        code = r['categorie_raison'] or 'autre'
        raisons.append({
            'categorie': code,
            'categorie_display': libelles.get(code, code),
            'count': r['count'],
            'pourcentage': _pct(r['count'], total),
        })

    reponse = {
        'total_non_executees': total,
        'raisons': raisons,
    }
    periode = _bloc_periode(date_debut, date_fin)
    if periode:
        reponse['periode'] = periode

    return Response(reponse)


# --------------------------------------------------------------------------
# 6. GET /stats/priorites/ (nouveau)
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def stats_priorites(request):
    """Répartition des tâches par priorité, avec fenêtre de dates optionnelle."""
    date_debut, date_fin = _parse_periode(request)

    tache_qs = _appliquer_periode(Tache.objects.all(), date_debut, date_fin)

    par_priorite = tache_qs.values('priorite').annotate(
        total=Count('id'),
        terminees=Count('id', filter=Q(status='completed')),
    )

    libelles = dict(Tache.PRIORITY_CHOICES)
    ordre = {code: i for i, (code, _) in enumerate(Tache.PRIORITY_CHOICES)}

    priorites = sorted(
        (
            {
                'priorite': p['priorite'],
                'priorite_display': libelles.get(p['priorite'], p['priorite']),
                'total': p['total'],
                'terminees': p['terminees'],
                'taux_execution': _pct(p['terminees'], p['total']),
            }
            for p in par_priorite
        ),
        key=lambda x: ordre.get(x['priorite'], 99)
    )

    reponse = {'priorites': priorites}
    periode = _bloc_periode(date_debut, date_fin)
    if periode:
        reponse['periode'] = periode

    return Response(reponse)


# --------------------------------------------------------------------------
# Inchangé : statistiques par semaine (modèle Semaine, pas dans la spec)
# --------------------------------------------------------------------------

@api_view(['GET'])
@permission_classes([IsManagerOrAdmin])
def statistiques_par_semaine(request, semaine_id=None):
    """Statistiques filtrées par semaine (modèle Semaine, indépendant de la fenêtre de dates)."""
    if semaine_id:
        taches = Tache.objects.filter(semaine_id=semaine_id)
    else:
        semaine_actuelle = Semaine.objects.filter(is_active=True).first()
        taches = Tache.objects.filter(semaine=semaine_actuelle) if semaine_actuelle else Tache.objects.none()

    par_status = taches.values('status').annotate(count=Count('id'))

    return Response({
        'semaine_id': semaine_id,
        'total': taches.count(),
        'par_status': list(par_status)
    })